# Cab Aggregator Project

This project is a backend API and Streamlit frontend for a cab aggregator service.

(You should add your own project description, setup instructions, etc., here)

...

---

## CI/CD Pipeline (Software Engineering Rubric)

This project uses GitHub Actions for Continuous Integration and Continuous Deployment (CI/CD). [cite_start]The pipeline is defined in `.github/workflows/ci-cd.yml` and is designed to meet the course rubric requirements[cite: 887].

### Pipeline Stages

The pipeline runs on every `push` and `pull_request` to the `main` branch and consists of the following stages:

1.  [cite_start]**Build** [cite: 890]
    * **Action:** Sets up the Python environment and installs all dependencies from `requirements.txt`.
    * **Purpose:** Ensures the project is buildable and all dependencies are correct.

2.  [cite_start]**Test** [cite: 891]
    * **Action:** Runs the entire `pytest` test suite.
    * **Purpose:** Verifies that all unit, integration, and system tests pass. The pipeline will fail if any test fails.

3.  [cite_start]**Coverage** [cite: 892]
    * **Action:** Runs `pytest-cov` to measure test coverage.
    * [cite_start]**Quality Gate:** The pipeline will **fail** if the total code coverage is **less than 75%**[cite: 897].
    * **Artifact:** Uploads the `coverage.xml` report.

4.  [cite_start]**Lint** [cite: 893]
    * **Action:** Runs `flake8` to perform static code analysis.
    * **Purpose:** Checks for Python syntax errors, undefined names, and code style issues.

5.  [cite_start]**Security** [cite: 894]
    * **Action:** Runs `bandit` to scan the codebase for common security vulnerabilities (e.g., hardcoded passwords, SQL injection risks).
    * **Purpose:** Ensures no critical security issues are introduced.

6.  [cite_start]**Deploy Artifact** [cite: 895]
    * **Action:** This stage only runs if **all** previous stages (Test, Coverage, Lint, Security) have passed.
    * [cite_start]**Purpose:** It bundles the project source code, all CI/CD reports (like coverage), and the README into a single `deployment-package.zip` file, as required by the rubric.
    * **Artifact:** Uploads the final `deployment-package.zip` which can be downloaded from the GitHub Actions run.

### [cite_start]Quality Gates [cite: 896]

The pipeline will fail and block merging if:
* Any `pytest` test fails.
* [cite_start]Code coverage is **below 75%**[cite: 897].
* `flake8` detects serious syntax errors.
* `bandit` finds high-severity security issues (this can be configured).