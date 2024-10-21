
import axios from 'axios';

export const cacheRepo = async (app, context) => {
  const repo = context.payload.repository;
  const repoName = repo.name;
  const ownerName = repo.owner.login;
  const repoUrl = repo.clone_url;
  const defaultBranch = repo.default_branch;

  // Get the latest commit SHA
  const latestCommit = await context.octokit.repos.listCommits({
    owner: ownerName,
    repo: repoName,
    sha: defaultBranch,
    per_page: 1,
  });

  const latestCommitSHA = latestCommit.data[0].sha;

  const data = {
    repo_url: repoUrl,
    owner: ownerName,
    repo_name: repoName,
    default_branch: defaultBranch,
    latest_commit_sha: latestCommitSHA,
  };

  try {
    const flaskResponse = await axios.post('http://localhost:5000/preprocess', data);
    if (flaskResponse.status !== 200) {
      throw new Error(`Failed to send data to Flask backend: ${flaskResponse.status} ${flaskResponse.statusText}`);
    }
    console.log('Repo info sent to Flask backend successfully.');
  } catch (error) {
    console.error('Error while sending repo info:', error);
  }
};
