# Ladybug

---

## Contains:
- Probot GitHub bot
- Flask backend


### Flask Backend

#### Set up GitHub bot
- Go to: ``https://github.com/apps/probot-test-ladybug``
- Install the app on the repository you want to use it on (Do not give it access to all repositories)

#### Development Setup

Initialize virtual environment & install dependencies:
```bash
python -m venv myenv
```
* On Windows: `myenv\Scripts\Activate`

* On Linux: `source myenv/bin/activate`

```bash
pip install -r requirements.txt
cd backend
python index.py
```
---

To install a new package:
```bash
pip install <package-name>
pip freeze > requirements.txt
```

To deactivate the virtual environment:
```bash
deactivate
```


