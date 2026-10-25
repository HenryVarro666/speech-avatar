"""Real Node execution of the browser export's acceptance/provenance contract."""
import json
from pathlib import Path
import subprocess
import unittest

MODULE = Path(__file__).resolve().parents[1]/'scripts/e1d_feedback.js'


class FeedbackExport(unittest.TestCase):
    def export(self, answers, mutate=None):
        data = {'manifest_sha256':'f'*64,'groups':[]}
        for role, offset in [('female',0),('male',2)]:
            data['groups'].append({'role':role,'clips':[
                {'id':role+'-'+label.lower(),'label':label,'sha256':str(offset+i+1)*64,
                 'trial_id':role+'-trial-'+label} for i,label in enumerate(['A','B'])]})
        if mutate:
            mutate(data)
        code = "const {buildFeedback}=require(process.argv[1]); const x=JSON.parse(process.argv[2]); console.log(JSON.stringify(buildFeedback(x.data,x.answers,{now:'2026-10-23T12:00:00Z',revealed:false})));"
        return subprocess.run(['node','-e',code,str(MODULE),json.dumps({'data':data,'answers':answers})],
                              text=True,capture_output=True)

    def test_defaults_do_not_claim_any_human_acceptance(self):
        result=self.export({})
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data['review_status'],'draft')
        self.assertIsNone(data['reviewer'])
        for role in data['roles'].values():
            self.assertIsNone(role['framing_preference'])
            self.assertEqual(role['av_acceptance'],{'A':None,'B':None})

    def test_preference_is_independent_of_acceptance_and_keeps_bindings(self):
        result=self.export({'reviewer':' QA fixture ', 'female':{'preference':'B','acceptance':'unreviewed',
                            'notes':' 2.64s 手入画 '},'male':{'preference':'A','acceptance':'neither'}})
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data['roles']['female']['av_acceptance'],{'A':None,'B':None})
        self.assertEqual(data['roles']['male']['av_acceptance'],{'A':False,'B':False})
        self.assertEqual(data['roles']['female']['notes'],'2.64s 手入画')
        self.assertEqual(data['roles']['male']['clips']['B']['sha256'],'4'*64)
        self.assertEqual(data['manifest_sha256'],'f'*64)
        self.assertFalse(data['revealed_before_export'])

    def test_explicit_acceptance_and_partial_review(self):
        result=self.export({'female':{'acceptance':'A','preference':'neither'}})
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data['roles']['female']['av_acceptance'],{'A':True,'B':False})
        self.assertEqual(data['roles']['female']['framing_preference'],'neither')
        self.assertEqual(data['roles']['male']['av_acceptance'],{'A':None,'B':None})

    def test_invalid_choice_or_media_binding_is_rejected(self):
        for args in [({'female':{'acceptance':'auto_pass'}},None),
                     ({},lambda d:d['groups'][0]['clips'][0].update(sha256='bad')),
                     ({},lambda d:d['groups'][0]['clips'][1].update(label='A'))]:
            result=self.export(*args)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Error',result.stderr)
