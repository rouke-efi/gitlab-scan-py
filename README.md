# GitLab Terraform File Analyzer

This project is designed to:
- Search for particular paths inside a GitLab group based on a specified `pattern`
- Search for `main.tf` and `version.json` files to fetch module names and their versions from the base layer of terraform custom modules within an organization
- Compile a JSON file with information about base modules and their current versions
- (TBD: Additional features to be added)

## How to Use

You can run the Python script using the provided Dockerfile.

### Set up Environment Variables

Create a `.env` file to store credentials and configuration:

```
GITLAB_URL=<gl-url>
GITLAB_GROUP_TOKEN=<token>
GITLAB_GROUP_PATH=<main group for search>
PATTERN=r'^terraform$' # not in use TBD
OUTPUT_DIR=/output
```

### Build the Image

Navigate to the Dockerfile directory and build the image:

```bash
docker build -t fetch-repos .
```

### Run Container

The container supports a `test` command for running unit tests. To run the main script, omit this argument.

```bash
docker run --rm --env-file .env -v /full/path/to/dir/on/your/local/host:/output fetch-repos:latest [test/module]
```
- [module] - is for searching and listing all modules found in all projects *iac-terraform* source and the versions of these modules

- [test] - is to run some unit tests for *gl_terraform_analyzer* script

Replace `/full/path/to/dir/on/your/local/host` with the actual path where you want the output JSON file to be saved.

## Notes

- Ensure your GitLab private token has the necessary permissions to access the specified group and its projects.
- The `PATTERN` environment variable should be a valid regular expression.
- The script will output its results to the directory specified in `OUTPUT_DIR`.