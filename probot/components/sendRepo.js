import axios from 'axios';

export const sendRepo = async (repo, context) => {
	// Extract owner and repo name from full_name
	const [ownerName, repoName] = repo.full_name.split('/');

	// Fetch the full repository details
	let fullRepo;
	try {
		const response = await context.octokit.repos.get({
			owner: ownerName,
			repo: repoName,
		});
		fullRepo = response.data;
	} catch (error) {
		console.error(`Failed to fetch repository details for ${ownerName}/${repoName}:`, error);
		return;
	}

	const repoUrl = fullRepo.clone_url;
	const defaultBranch = fullRepo.default_branch;

  // Get the latest commit SHA
	let latestCommitSHA;
	try {
		const latestCommit = await context.octokit.repos.listCommits({
			owner: ownerName,
			repo: repoName,
			sha: defaultBranch,
			per_page: 1,
		});
		latestCommitSHA = latestCommit.data[0].sha;
	} catch (error) {
		console.error(`Failed to fetch latest commit for ${ownerName}/${repoName}:`, error);
		return;
	}

  const data = {
    repo_url: repoUrl,
    owner: ownerName,
    repo_name: repoName,
    default_branch: defaultBranch,
    latest_commit_sha: latestCommitSHA,
  };

  try {
	  const flaskResponse = await axios.post('http://localhost:5000/initialization', data);
    if (flaskResponse.status !== 200) {
      throw new Error(`Failed to send data to Flask backend: ${flaskResponse.status} ${flaskResponse.statusText}`);
    }
    console.log('Repo info sent to Flask backend successfully.');
  } catch (error) {
    console.error('Error while sending repo info:', error);
  }
};
