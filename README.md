# 📊 Advanced Convertible Preferred Stock Modeler

A web-based financial analytics application built with **Python** and **Streamlit**. This dashboard helps investors model complex conversion collar thresholds, visualize total return curve profiles, calculate accurate cash flow IRR/CAGR metrics, and use a secure LLM text parser to automatically pull asset variables from SEC filings.

---

## 🛠️ Local Installation & Development Guide

Follow these steps to run the analytics application on your local computer.

### 1. Clone or Download the Project
Ensure you have the application code files organized in a single folder:
```bash
mkdir convertible-modeler
cd convertible-modeler
# Place your app.py and requirements.txt files into this directory
```

### 2. Set Up a Virtual Environment (Recommended)
Isolate your package dependencies to keep your system clean:
```bash
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows (Command Prompt):
venv\Scripts\activate
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

### 3. Install Package Dependencies
Install the required financial math, charting, and streaming libraries using pip:
```bash
pip install -r requirements.txt
```

### 4. Create the Local Secrets File
The application requires a secure runtime token file to interact with the Hugging Face Serverless Inference API without exposing keys inside public code. 

Create a hidden folder named `.streamlit` and add a `secrets.toml` file inside it:
```bash
mkdir .streamlit
touch .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` in your text editor and add your Hugging Face API key exactly like this:
```toml
# .streamlit/secrets.toml
HF_TOKEN = "hf_YOUR_ACTUAL_FREE_READ_TOKEN_HERE"
```
*(Note: You can get a free read-only API token by registering an account at [huggingface.co](https://huggingface.co) and navigating to Settings -> Access Tokens).*

### 5. Launch the Local Application Server
Run the Streamlit execution engine to spin up your browser-based application interface:
```bash
streamlit run app.py
```
The console will output a local network address (typically `http://localhost:8501`). Open this URL in any browser to interact with the application.

---

## 🚀 Production Deployment Guide (Streamlit Community Cloud)

You can host this tool on the web completely for free so other users can access it without executing terminal commands.

### 1. Push Code to GitHub
1. Create a free account or sign in to [GitHub](https://github.com).
2. Create a new **public or private** repository named `convertible-modeler`.
3. Upload your production files into the repository:
   * `app.py`
   * `requirements.txt`
   * *(Do NOT upload the `.streamlit` folder or your `secrets.toml` file to GitHub)*

### 2. Connect to Streamlit Community Cloud
1. Navigate to [share.streamlit.io](https://streamlit.io) and log in using your GitHub account permissions.
2. Click the **"Create app"** or **"New app"** button in the dashboard workspace.
3. Select your `convertible-modeler` repository from the dropdown menu, select the `main` or `master` branch, and set the Main file path entry fields to `app.py`.

### 3. Configure Production Cloud Secrets
To ensure the LLM text parser works on your live web address, you must inject your API key into Streamlit's encrypted cloud workspace container:

1. Before clicking deploy, click on the **"Advanced settings..."** button on the deployment configuration page (or click the gear settings icon on your dashboard app panel later).
2. Find the **"Secrets"** text area section.
3. Paste your key configuration properties exactly as formatted below:
   ```toml
   HF_TOKEN = "hf_YOUR_ACTUAL_FREE_READ_TOKEN_HERE"
   ```
4. Click **"Save"**.

### 4. Finalize Deployment
Click the **"Deploy!"** button. Streamlit will instantly provision an isolated engine container, download the libraries from `requirements.txt`, inject your `HF_TOKEN` securely into the background runtime framework, and publish your secure live tracking link.

## 🔍 Features & Operational Workflow

### Real-Time SEC Discovery Engine
The sidebar contains an automated portal into the **SEC EDGAR Index Registry**. By inputting a corporate email address (required under fair-access rules by the SEC) and filtering by an underlying ticker, the application will:
1. Programmatically scan SEC endpoints for recent `424B5` and `424B2` prospectus filings.
2. Locate keyword anchors matching conversion threshold parameters.
3. Automatically slice and clean the document's HTML structures down into a text block ready for parsing via the **Hugging Face AI Extractor**.

### Parallel Scenario Analysis Table
Located at the bottom of the interface workspace under **Step 3**, this financial matrix maps portfolio metrics across multiple simultaneous price targets. The framework scales points to display:
*   A **-30% and -15% market stress-test** configuration.
*   The **exact inflection barriers** of the underlying structural lower floor and upper cap collar walls.
*   **Outperformance trajectories (+15% / +30%)**, mapping out changing conversion ratio adjustments, absolute holding returns, and compounded annualized internal rate of return variations simultaneously.

