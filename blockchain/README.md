# Steps to clone and run it locally
**Make sure your python version is Python 3.10.12.**
1. pip install -r requirements.txt
2. **Windows** user search sys.path.append("/Users/my/Desktop/blockchain") and replace all it with your system path. 
   **On Linux machine**, make sure you copy the complete path from /home/username/Desktop/blockchain
3. Open VSCODE and go to blockchain.py file inside the core directory and run it. If you get any error related to config file then try to run it in debug mode. Click on run -> Start debugging. You don't have to set the breakpoint. Sometimes config.ini does not work in batch mode. Keep that in mind.
4. Goto http://127.0.0.1:5900/ and your Blockchain is up and running now.
