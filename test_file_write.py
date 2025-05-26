import json
import os

def test_file_write():
    """Test if we can write to the course list file"""
    
    test_data = ["Test Course 1", "Test Course 2", "Test Course 3"]
    file_path = "static/course_list.json"
    
    print(f"🔍 Testing file write to: {file_path}")
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📂 Static directory exists: {os.path.exists('static')}")
    print(f"📄 File exists before write: {os.path.exists(file_path)}")
    
    try:
        # Try to write test data
        with open(file_path, "w") as f:
            json.dump(test_data, f, indent=2)
        
        print("✅ File write successful")
        
        # Try to read it back
        with open(file_path, "r") as f:
            data = json.load(f)
        
        print(f"📖 Read back: {data}")
        print(f"📏 Length: {len(data)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_file_write()
