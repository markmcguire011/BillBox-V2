#!/usr/bin/env python3
"""
BillBox Project Launcher
Unified script to start the entire BillBox application with all necessary services
"""

import os
import sys
import time
import signal
import subprocess
import platform
import webbrowser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class BillBoxLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.ocr_dir = self.project_root / "services" / "ocr"
        
        self.processes = []
        self.shutdown_event = threading.Event()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n{Colors.WARNING}Received shutdown signal. Cleaning up...{Colors.ENDC}")
        self.shutdown()
        
    def print_banner(self):
        """Print application banner"""
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════════╗
║                  BillBox                     ║
║           Invoice Processing System          ║
╚══════════════════════════════════════════════╝
{Colors.ENDC}
"""
        print(banner)
        
    def check_python_version(self):
        """Verify Python version compatibility"""
        print(f"{Colors.OKBLUE}🔍 Checking Python version...{Colors.ENDC}")
        
        if sys.version_info < (3, 8):
            print(f"{Colors.FAIL}❌ Python 3.8+ required. Current version: {sys.version}{Colors.ENDC}")
            return False
            
        print(f"{Colors.OKGREEN}✅ Python {sys.version.split()[0]} detected{Colors.ENDC}")
        return True
        
    def check_directories(self):
        """Verify project structure"""
        print(f"{Colors.OKBLUE}🔍 Checking project structure...{Colors.ENDC}")
        
        required_dirs = [
            self.backend_dir,
            self.frontend_dir,
            self.ocr_dir
        ]
        
        for directory in required_dirs:
            if not directory.exists():
                print(f"{Colors.FAIL}❌ Missing directory: {directory}{Colors.ENDC}")
                return False
            print(f"{Colors.OKGREEN}✅ Found: {directory.name}/{Colors.ENDC}")
                
        return True
        
    def check_environment_file(self):
        """Check for environment configuration"""
        print(f"{Colors.OKBLUE}🔍 Checking environment configuration...{Colors.ENDC}")
        
        env_file = self.backend_dir / ".env"
        env_example = self.backend_dir / ".env.example"
        
        if not env_file.exists():
            if env_example.exists():
                print(f"{Colors.WARNING}⚠️  No .env file found. Please copy .env.example to .env and configure:{Colors.ENDC}")
                print(f"   cp {env_example} {env_file}")
                print(f"{Colors.WARNING}   Then edit .env with your Google OAuth credentials{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️  No environment configuration found{Colors.ENDC}")
            return False
            
        print(f"{Colors.OKGREEN}✅ Environment file found{Colors.ENDC}")
        return True
        
    def check_backend_dependencies(self):
        """Check if backend dependencies are installed"""
        print(f"{Colors.OKBLUE}🔍 Checking backend dependencies...{Colors.ENDC}")
        
        requirements_file = self.backend_dir / "requirements.txt"
        if not requirements_file.exists():
            print(f"{Colors.FAIL}❌ requirements.txt not found{Colors.ENDC}")
            return False
            
        # Try importing key dependencies
        try:
            import fastapi
            import uvicorn
            print(f"{Colors.OKGREEN}✅ FastAPI dependencies available{Colors.ENDC}")
            return True
        except ImportError as e:
            print(f"{Colors.WARNING}⚠️  Missing backend dependencies. Installing...{Colors.ENDC}")
            return self.install_backend_dependencies()
            
    def install_backend_dependencies(self):
        """Install backend dependencies"""
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(self.backend_dir / "requirements.txt")]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"{Colors.OKGREEN}✅ Backend dependencies installed{Colors.ENDC}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}❌ Failed to install dependencies: {e}{Colors.ENDC}")
            return False
            
    def check_ocr_service(self):
        """Check OCR service availability"""
        print(f"{Colors.OKBLUE}🔍 Checking OCR service...{Colors.ENDC}")
        
        ocr_main = self.ocr_dir / "billbox_ocr.py"
        if not ocr_main.exists():
            print(f"{Colors.FAIL}❌ OCR service not found{Colors.ENDC}")
            return False
            
        # Check if preprocessing module is built
        try:
            sys.path.append(str(self.ocr_dir))
            import billbox_ocr
            print(f"{Colors.OKGREEN}✅ OCR service available{Colors.ENDC}")
            return True
        except ImportError:
            print(f"{Colors.WARNING}⚠️  OCR preprocessing module not built. Basic OCR will be used.{Colors.ENDC}")
            return True
            
    def start_backend(self):
        """Start the FastAPI backend"""
        print(f"{Colors.OKBLUE}🚀 Starting backend server...{Colors.ENDC}")
        
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(("Backend", process))
            
            # Wait for server to start
            for i in range(30):  # 30 second timeout
                if process.poll() is not None:
                    print(f"{Colors.FAIL}❌ Backend failed to start{Colors.ENDC}")
                    return False
                    
                try:
                    import requests
                    response = requests.get("http://localhost:8000/health", timeout=1)
                    if response.status_code == 200:
                        print(f"{Colors.OKGREEN}✅ Backend server running on http://localhost:8000{Colors.ENDC}")
                        return True
                except:
                    pass
                    
                time.sleep(1)
                
            print(f"{Colors.FAIL}❌ Backend startup timeout{Colors.ENDC}")
            return False
            
        except Exception as e:
            print(f"{Colors.FAIL}❌ Failed to start backend: {e}{Colors.ENDC}")
            return False
            
    def start_frontend(self):
        """Start the frontend server"""
        print(f"{Colors.OKBLUE}🚀 Starting frontend server...{Colors.ENDC}")
        
        # Try different server options
        server_commands = [
            [sys.executable, "-m", "http.server", "3000"],
            ["python3", "-m", "http.server", "3000"],
            ["python", "-m", "http.server", "3000"]
        ]
        
        for cmd in server_commands:
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=self.frontend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # Test if server started
                time.sleep(2)
                if process.poll() is None:
                    self.processes.append(("Frontend", process))
                    print(f"{Colors.OKGREEN}✅ Frontend server running on http://localhost:3000{Colors.ENDC}")
                    return True
                    
            except FileNotFoundError:
                continue
                
        print(f"{Colors.FAIL}❌ Failed to start frontend server{Colors.ENDC}")
        return False
        
    def open_browser(self):
        """Open the application in the default browser"""
        print(f"{Colors.OKBLUE}🌐 Opening application in browser...{Colors.ENDC}")
        try:
            webbrowser.open("http://localhost:3000")
            print(f"{Colors.OKGREEN}✅ Browser opened{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  Could not open browser automatically: {e}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}🔗 Please open: http://localhost:3000{Colors.ENDC}")
            
    def monitor_processes(self):
        """Monitor running processes"""
        print(f"\n{Colors.OKCYAN}📊 Monitoring services... Press Ctrl+C to stop{Colors.ENDC}")
        print(f"{Colors.OKCYAN}🌐 Frontend: http://localhost:3000{Colors.ENDC}")
        print(f"{Colors.OKCYAN}🔧 Backend API: http://localhost:8000{Colors.ENDC}")
        print(f"{Colors.OKCYAN}📖 API Docs: http://localhost:8000/docs{Colors.ENDC}")
        
        try:
            while not self.shutdown_event.is_set():
                # Check if processes are still running
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"{Colors.FAIL}❌ {name} process stopped unexpectedly{Colors.ENDC}")
                        self.shutdown()
                        return
                        
                time.sleep(5)
                
        except KeyboardInterrupt:
            pass
            
    def shutdown(self):
        """Gracefully shutdown all processes"""
        print(f"\n{Colors.WARNING}🛑 Shutting down services...{Colors.ENDC}")
        
        self.shutdown_event.set()
        
        for name, process in self.processes:
            try:
                print(f"{Colors.WARNING}🔄 Stopping {name}...{Colors.ENDC}")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"{Colors.OKGREEN}✅ {name} stopped{Colors.ENDC}")
                except subprocess.TimeoutExpired:
                    print(f"{Colors.WARNING}⏰ Force killing {name}...{Colors.ENDC}")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                print(f"{Colors.FAIL}❌ Error stopping {name}: {e}{Colors.ENDC}")
                
        print(f"{Colors.OKGREEN}✅ All services stopped{Colors.ENDC}")
        
    def run(self):
        """Main execution flow"""
        self.print_banner()
        
        # Pre-flight checks
        checks = [
            ("Python Version", self.check_python_version),
            ("Project Structure", self.check_directories),
            ("Environment Config", self.check_environment_file),
            ("Backend Dependencies", self.check_backend_dependencies),
            ("OCR Service", self.check_ocr_service)
        ]
        
        print(f"{Colors.BOLD}🔧 Running pre-flight checks...{Colors.ENDC}")
        for check_name, check_func in checks:
            if not check_func():
                print(f"\n{Colors.FAIL}❌ Pre-flight check failed: {check_name}{Colors.ENDC}")
                return False
                
        print(f"\n{Colors.OKGREEN}✅ All pre-flight checks passed!{Colors.ENDC}")
        
        # Start services
        print(f"\n{Colors.BOLD}🚀 Starting services...{Colors.ENDC}")
        
        if not self.start_backend():
            return False
            
        if not self.start_frontend():
            return False
            
        # Open browser
        time.sleep(2)
        self.open_browser()
        
        # Monitor
        self.monitor_processes()
        
        return True

def main():
    """Entry point"""
    launcher = BillBoxLauncher()
    
    try:
        success = launcher.run()
        if not success:
            print(f"\n{Colors.FAIL}❌ Failed to start BillBox{Colors.ENDC}")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Unexpected error: {e}{Colors.ENDC}")
        return 1
    finally:
        launcher.shutdown()
        
    print(f"\n{Colors.OKCYAN}👋 Thanks for using BillBox!{Colors.ENDC}")
    return 0

if __name__ == "__main__":
    sys.exit(main())