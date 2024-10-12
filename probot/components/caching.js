// caching.js
import AdmZip from 'adm-zip';
import path from 'path';
import fs from 'fs';
import fetch from 'node-fetch';

// need to add variable to make a route / env variable

export const cacheRepo = async (app, context) => {
    const repo = context.payload.repository;
    const repoName = repo.name;
    const hostName = repo.owner.login;
    const defaultBranch = repo.default_branch; // e.g., 'master'

    console.log('Caching repo:', repoName);
    console.log('Owner:', hostName);
    console.log('Default branch:', defaultBranch);

    try {
        const zipResponse = await context.octokit.repos.downloadZipballArchive({
            owner: hostName,
            repo: repoName,
            ref: defaultBranch,
        }, {
            // Ensure the response is returned as a buffer
            headers: {
                'Accept': 'application/vnd.github.v3.raw'
            },
            request: {
                // Specify response type if necessary
                responseType: 'arraybuffer'
            }
        });

        // Convert the response data to a Buffer
        const buffer = Buffer.from(zipResponse.data, 'binary');

        // Define the directory to cache
        const cacheDir = path.resolve(`./cached_repos/${repoName}`);
        fs.mkdirSync(cacheDir, { recursive: true });

        // Store the zip file
        const zipPath = path.resolve(cacheDir, `${repoName}.zip`);
        fs.writeFileSync(zipPath, buffer);

        console.log(`Repo ${repoName} cached successfully at ${zipPath}`);

        const zip = new AdmZip(zipPath);
        zip.extractAllTo(cacheDir, true);

        console.log(`Repo ${repoName} extracted successfully to ${cacheDir}`);

        // Send zip to Flask backend
        const flask_response = await fetch(`http://127.0.0.1:5000/preprocess`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: cacheDir }),
        });

        if (!flask_response.ok) {
            throw new Error(`Failed to send data to Flask backend: ${flask_response.status} ${flask_response.statusText}`);
        }

        console.log('Data sent to Flask backend successfully.');

    } catch (error) {
        console.error('Error while caching repo:', error);
    }
};
