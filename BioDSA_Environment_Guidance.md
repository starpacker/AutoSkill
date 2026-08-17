# BioDSA Python 3.12 Environment Setup Guidance

This document describes how to activate and use the Python 3.12 environment created specifically for the **BioDSA** evaluation framework on server1.

## 1. Environment Details
- **Location**: /data/yjh/conda_envs/biodsa_env
- **Python Version**: 3.12.x
- **Purpose**: To run the BioDSA agent testing and benchmarking framework, which strictly requires Python >= 3.12.

## 2. How to Activate the Environment
When you SSH into server1, Conda is available but you may need to initialize it or source it first. To properly activate your new environment, run the following commands on the server:

`ash
# 1. Source the Conda profile
source /usr/local/anaconda3/etc/profile.d/conda.sh

# 2. Activate the BioDSA environment
conda activate biodsa_env

# 3. Verify your Python version
python --version
# Expected output: Python 3.12.x
`

## 3. How to Deploy the BioDSA Framework
Once the environment is activated, you can proceed to install the BioDSA framework dependencies using pipenv. 

`ash
# 1. Navigate to the BioDSA directory
cd /data/yjh/BioDSA

# 2. Install pipenv (if not already installed in this env)
python -m pip install pipenv

# 3. Install all framework dependencies via pipenv
python -m pipenv install
`

## 4. Next Steps: Running Evaluations
After successfully installing the dependencies, you can start running evaluations using the BioDSA scripts located in /data/yjh/BioDSA. Ensure you always run these scripts from within the activated iodsa_env conda environment.
