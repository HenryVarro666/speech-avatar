/** WebGL2 texture-puppet renderer, not a neural video generator. */
const vert=`#version 300 es
in vec2 position;out vec2 uv;void main(){uv=position*.5+.5;gl_Position=vec4(position,0,1);}`;
const frag=`#version 300 es
precision highp float;in vec2 uv;out vec4 color;uniform sampler2D baseTex;uniform sampler2D mouthTex;uniform sampler2D eyeTex;uniform vec4 mouthRect;uniform vec4 eyeRect;uniform float pose;uniform float amount;uniform float blink;
float mask(vec2 t){return smoothstep(0.,.13,t.x)*smoothstep(0.,.13,t.y)*(1.-smoothstep(.87,1.,t.x))*(1.-smoothstep(.87,1.,t.y));}
void main(){vec2 p=vec2(uv.x,1.-uv.y);vec3 c=texture(baseTex,uv).rgb;vec2 m=(p-mouthRect.xy)/mouthRect.zw;if(all(greaterThanEqual(m,vec2(0)))&&all(lessThanEqual(m,vec2(1)))){vec3 a=texture(mouthTex,vec2((pose+m.x)/5.,1.-m.y)).rgb;c=mix(c,a,mask(m)*amount);}vec2 e=(p-eyeRect.xy)/eyeRect.zw;if(all(greaterThanEqual(e,vec2(0)))&&all(lessThanEqual(e,vec2(1)))){vec3 a=texture(eyeTex,vec2((1.+e.x)/2.,1.-e.y)).rgb;c=mix(c,a,mask(e)*blink);}color=vec4(c,1);}`;
export class PortraitGL {
 constructor(canvas,onstate){this.canvas=canvas;this.onstate=onstate;this.images=new Map();this.ok=false;canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.ok=false;onstate(false,'context_lost')});canvas.addEventListener('webglcontextrestored',()=>{this.init(this.asset).catch(e=>onstate(false,e.message))})}
 async init(asset){
 const version=this.version=(this.version||0)+1;
 if(this.asset===asset&&this.ok)return;
 this.asset=asset;
 await Promise.all(['base','mouth','eyes'].map(async key=>{if(!this.images.has(asset[key])){const img=await new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error('Texture failed: '+asset[key]));im.src=asset[key]});this.images.set(asset[key],img)}}));
 if(version!==this.version)return;
 const gl=this.canvas.getContext('webgl2',{alpha:false,antialias:false});if(!gl||gl.isContextLost())throw Error('WebGL2 unavailable or context lost');this.gl=gl;
 for(const t of this.textures||[])gl.deleteTexture(t);if(this.program)gl.deleteProgram(this.program);if(this.buffer)gl.deleteBuffer(this.buffer);this.textures=[];
 const shader=(type,s)=>{const a=gl.createShader(type);gl.shaderSource(a,s);gl.compileShader(a);if(!gl.getShaderParameter(a,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(a));return a};const p=gl.createProgram();const vs=shader(gl.VERTEX_SHADER,vert),fs=shader(gl.FRAGMENT_SHADER,frag);gl.attachShader(p,vs);gl.attachShader(p,fs);gl.linkProgram(p);gl.deleteShader(vs);gl.deleteShader(fs);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));gl.useProgram(p);this.program=p;
 const buf=this.buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);const a=gl.getAttribLocation(p,'position');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
 for(const [i,key,uniform] of [[0,'base','baseTex'],[1,'mouth','mouthTex'],[2,'eyes','eyeTex']]){const img=this.images.get(asset[key]),t=gl.createTexture();this.textures.push(t);gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,t);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,img);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.uniform1i(gl.getUniformLocation(p,uniform),i)}
 gl.uniform4fv(gl.getUniformLocation(p,'mouthRect'),asset.mouthRect);gl.uniform4fv(gl.getUniformLocation(p,'eyeRect'),asset.eyeRect);this.locs=Object.fromEntries(['pose','amount','blink'].map(k=>[k,gl.getUniformLocation(p,k)]));const dbg=gl.getExtension('WEBGL_debug_renderer_info');this.renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);this.loseExt=gl.getExtension('WEBGL_lose_context');this.ok=true;this.onstate(true,'context_ready');}
 draw(pose,amount,blink){if(!this.ok)return false;const g=this.gl;g.useProgram(this.program);g.viewport(0,0,this.canvas.width,this.canvas.height);g.uniform1f(this.locs.pose,pose);g.uniform1f(this.locs.amount,amount);g.uniform1f(this.locs.blink,blink);g.drawArrays(g.TRIANGLE_STRIP,0,4);return true}
 lose(){if(this.loseExt)this.loseExt.loseContext();else{this.ok=false;this.onstate(false,'renderer_disabled')}}
 restore(){if(this.loseExt&&this.gl.isContextLost())this.loseExt.restoreContext();else this.init(this.asset).catch(e=>this.onstate(false,e.message))}
}
