/* Shared by the local review page and CPU contract tests. */
function buildFeedback(preview, answers = {}, options = {}) {
  const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/i.test(value);
  if (!digest(preview.manifest_sha256) || !Array.isArray(preview.groups) || preview.groups.length !== 2) {
    throw new Error('Missing frozen review bindings');
  }
  const roles = {};
  const ids = new Set();
  for (const group of preview.groups) {
    if (!['female', 'male'].includes(group.role) || roles[group.role] || group.clips.length !== 2) {
      throw new Error('Invalid role bindings');
    }
    const clips = {};
    for (const clip of group.clips) {
      if (!['A', 'B'].includes(clip.label) || clips[clip.label] || !digest(clip.sha256) ||
          !clip.id || !clip.trial_id || ids.has(clip.id)) {
        throw new Error('Invalid clip bindings');
      }
      ids.add(clip.id);
      clips[clip.label] = {id: clip.id, trial_id: clip.trial_id, sha256: clip.sha256};
    }
    const answer = answers[group.role] || {};
    const preference = answer.preference ?? 'unreviewed';
    const acceptance = answer.acceptance ?? 'unreviewed';
    if (!['unreviewed', 'A', 'B', 'no_difference', 'neither'].includes(preference) ||
        !['unreviewed', 'A', 'B', 'both', 'neither'].includes(acceptance)) {
      throw new Error('Invalid review choice');
    }
    roles[group.role] = {
      framing_preference: preference === 'unreviewed' ? null : preference,
      av_acceptance: {
        A: acceptance === 'unreviewed' ? null : ['A', 'both'].includes(acceptance),
        B: acceptance === 'unreviewed' ? null : ['B', 'both'].includes(acceptance),
      },
      notes: String(answer.notes || '').trim() || null,
      clips,
    };
  }
  return {
    schema_version: 1,
    experiment_id: '2026-10-23-e1d-reference-framing',
    review_status: 'draft',
    created_utc: options.now || new Date().toISOString(),
    reviewer: String(answers.reviewer || '').trim() || null,
    manifest_sha256: preview.manifest_sha256,
    revealed_before_export: options.revealed === true,
    roles,
  };
}

if (typeof module !== 'undefined' && module.exports) module.exports = {buildFeedback};
