module.exports = {
  ci: {
    collect: {
      staticDistDir: './dist',
      url: ['/index.html'],
      numberOfRuns: 1,
    },
    upload: {
      target: 'filesystem',
      outputDir: '.lighthouseci',
    },
  },
};
