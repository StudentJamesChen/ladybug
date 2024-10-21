import axios from 'axios';

export const cacheRepo = async (app, context) => {
  const repo = context.payload.repository;
  const repoName = repo.name;
  const hostName = repo.owner.login;
  const defaultBranch = repo.default_branch;

  console.log('Caching repo:', repoName);

  try {
    const zipResponse = await context.octokit.repos.downloadZipballArchive({
      owner: hostName,
      repo: repoName,
      ref: defaultBranch,
    });

    // Send the zip data directly to Flask backend
    const flaskResponse = await axios.post('http://localhost:5000/preprocess', zipResponse.data, {
      headers: {
        'Content-Type': 'application/zip',
      },
      maxContentLength: Infinity,
      maxBodyLength: Infinity,
    });

    if (flaskResponse.status !== 200) {
      throw new Error(`Failed to send data to Flask backend: ${flaskResponse.status} ${flaskResponse.statusText}`);
    }

    console.log('Data sent to Flask backend successfully.');
  } catch (error) {
    console.error('Error while caching repo:', error);
  }
};
