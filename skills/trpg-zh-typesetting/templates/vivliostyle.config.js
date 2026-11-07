// Vivliostyle config: one entry per build call is selected by build.py via VS_ENTRY / VS_OUT env vars.
module.exports = {
  title: process.env.VS_TITLE || 'TRPG 中文排版',
  language: 'zh-CN',
  entry: [process.env.VS_ENTRY || 'build/ch1.html'],
  output: [process.env.VS_OUT || 'work/pdf/ch1.pdf'],
  workspaceDir: '.',
  timeout: 1800000,
};
