import requests
import sys
import os

def download_file(username, token, remote_path, local_dir):
    host = 'www.pythonanywhere.com'
    headers = {'Authorization': f'Token {token}'}
    api_url = f'https://{host}/api/v0/user/{username}/files/path{remote_path}'
    
    filename = os.path.basename(remote_path)
    local_path = os.path.join(local_dir, filename)
    
    print(f"⬇️ Downloading: {remote_path} -> {local_path}")
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print("✅ Download Complete")
    else:
        print(f"❌ Error: {response.status_code}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sync_pa.py <username> <token>")
        sys.exit(1)
    
    os.makedirs('pa_backup', exist_ok=True)
    
    # Try downloading the zips found
    download_file(sys.argv[1], sys.argv[2], f'/home/{sys.argv[1]}/englishbus_deploy.zip', 'pa_backup')
    download_file(sys.argv[1], sys.argv[2], f'/home/{sys.argv[1]}/myzipfile.zip', 'pa_backup')


