import subprocess
import sys
import signal
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# Global variables
LOG_FILE_PATH = "path/to/your/log/file.log"
KEYWORDS_TO_COUNT = ["ERROR", "HTTP"]  # Keywords to count occurrences
REPORT_SIZE = 5  # Number of top entries to include in the summary report
ANALYSIS_WINDOW = timedelta(hours=1)  # Time window for log analysis (e.g., last hour)

# Email configuration (Update with your SMTP server details)
SMTP_SERVER = 'smtp.yourserver.com'
SMTP_PORT = 587
SMTP_USERNAME = 'your_email@example.com'
SMTP_PASSWORD = 'your_email_password'
ALERT_EMAIL = 'recipient@example.com'

# Signal handler for Ctrl+C
def signal_handler(sig, frame):
    print("\nStopping log monitoring...")
    generate_summary_report()  # Generate summary report before exiting
    sys.exit(0)

# Function to continuously monitor log file using tail command
def monitor_log_file():
    try:
        # Open tail command to monitor the log file in real time
        tail_process = subprocess.Popen(['tail', '-F', LOG_FILE_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        print(f"Monitoring log file: {LOG_FILE_PATH}")
        print("Press Ctrl+C to stop monitoring.")

        # Continuous loop to read and process new log entries
        while True:
            line = tail_process.stdout.readline().strip()
            if line:
                process_log_entry(line)
                analyze_log_over_time()
                check_critical_events(line)
    except FileNotFoundError:
        print(f"Error: Log file '{LOG_FILE_PATH}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)
    finally:
        # Close tail process when done
        tail_process.terminate()

# Function to process each log entry
def process_log_entry(entry):
    # Count occurrences of keywords in the log entry
    entry_lower = entry.lower()
    keyword_counts = {keyword: entry_lower.count(keyword.lower()) for keyword in KEYWORDS_TO_COUNT}
    
    # Display the log entry and keyword counts
    print(f"Log Entry: {entry}")
    print("Keyword Counts:")
    for keyword, count in keyword_counts.items():
        print(f"{keyword}: {count}")
    print("=" * 30)  # Separator

# Function to analyze log entries over a defined time window
def analyze_log_over_time():
    try:
        with open(LOG_FILE_PATH, "r") as file:
            end_time = datetime.now()
            start_time = end_time - ANALYSIS_WINDOW

            # Read log entries within the analysis window
            relevant_entries = []
            for line in file:
                entry_time_str = line[:19]  # Extract timestamp from the log entry
                entry_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
                if start_time <= entry_time <= end_time:
                    relevant_entries.append(line.lower())

            # Analyze keyword counts over the specified time window
            keyword_counts = {keyword: sum(entry.count(keyword.lower()) for entry in relevant_entries) for keyword in KEYWORDS_TO_COUNT}
            
            print(f"Analysis over the last {ANALYSIS_WINDOW}:")
            print("Keyword Counts:")
            for keyword, count in keyword_counts.items():
                print(f"{keyword}: {count}")
            print("=" * 30)  # Separator
    except FileNotFoundError:
        print(f"Error: Log file '{LOG_FILE_PATH}' not found.")
    except Exception as e:
        print(f"Error occurred during log analysis: {str(e)}")

# Function to check for critical events and send email alerts
def check_critical_events(entry):
    try:
        for keyword in KEYWORDS_TO_COUNT:
            if keyword.lower() in entry.lower():
                send_email_alert(keyword, entry)
                break
    except Exception as e:
        print(f"Error occurred while checking critical events: {str(e)}")

# Function to send email alert for critical events
def send_email_alert(keyword, log_entry):
    try:
        subject = f"Critical Log Event: {keyword}"
        body = f"The following log entry triggered a critical event:\n\n{log_entry}"

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SMTP_USERNAME
        msg['To'] = ALERT_EMAIL

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, ALERT_EMAIL, msg.as_string())
        server.quit()

        print(f"Email alert sent for critical event: {keyword}")
    except Exception as e:
        print(f"Error occurred while sending email alert: {str(e)}")

# Function to generate summary report based on keyword counts
def generate_summary_report():
    try:
        with open(LOG_FILE_PATH, "r") as file:
            content = file.read().lower()
            keyword_counts = {keyword: content.count(keyword.lower()) for keyword in KEYWORDS_TO_COUNT}
            sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            print("Summary Report:")
            for keyword, count in sorted_keywords[:REPORT_SIZE]:
                print(f"{keyword}: {count}")
    except FileNotFoundError:
        print(f"Error: Log file '{LOG_FILE_PATH}' not found.")
    except Exception as e:
        print(f"Error occurred while generating summary report: {str(e)}")

if __name__ == "__main__":
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Start monitoring log file
    try:
        monitor_log_file()
    except KeyboardInterrupt:
        print("\nLog monitoring stopped.")
        generate_summary_report()
