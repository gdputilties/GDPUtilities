import os
import re
import smtplib
import socket
import ssl
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email_with_results(host, smtp_host, smtp_port, sender_email, sender_email_pass, to_email_addresses,
                            cc_email_address,
                            bcc_email_address, main_body):
    subject = "Alert: " + host + " commands status"
    footer_text = "Regards,<br>GDP Team<br><br>Note: This is auto generated email please do-not reply."
    body_msg = "<html><body>Hi Team,<br><br>Please find below list of commands executed in the host " + host + "<br><br>"
    body_msg = body_msg + main_body + "<br><br>" + footer_text
    message = MIMEMultipart()
    to_emails = to_email_addresses.split(",")
    cc_emails = cc_email_address.split(",")
    bcc_emails = bcc_email_address.split(",")
    recepient = to_emails + cc_emails + bcc_emails
    message["From"] = sender_email
    message["To"] = ", ".join(to_emails)
    message["Cc"] = ", ".join(cc_emails)
    message["Bcc"] = ", ".join(bcc_emails)
    message["Subject"] = subject
    message.attach(MIMEText(body_msg, "html"))
    mail_body = message.as_string()
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        try:
            server.login(sender_email, sender_email_pass)
        except Exception:
            print("Unable to login to smtp server")
            traceback.print_exc()
        try:
            server.sendmail(sender_email, recepient, mail_body)
            print("Email sent successfully")
        except Exception:
            print("Unable to send email")
            traceback.print_exc()
        server.quit()


commands = "date,hostname,uptime,df -hP /boot,df -hP /home,df -hP /root,top"
command_list = commands.split(",")
danger_font_start_tag = "<font color='red'>"
danger_font_end_tag = "</font>"
header_text = "<table border=1><tr bgcolor=yellow><th>Host</th><th>Command</th><th>Result</th></tr>"
cmd_count = len(command_list)
host = socket.gethostname()
body_text = ""
cmd_line_count = 0
for cmd in command_list:
    print(cmd)
    org_cmd = cmd
    top_loaded = False
    if "df " in cmd:
        cmd = cmd + " | awk '{print $5}'"
    elif "top" in cmd:
        cmd = cmd + " -n 1"
    stream = os.popen(cmd)
    output = stream.readlines()
    # print("output: ", output)
    load_avg_val = ""
    cpu_utilization = ""
    for result in output:
        result = result.strip()
        if result == "":
            continue
        if "df -hP" in cmd:
            if "Use%" not in result:
                print("Command", cmd, " output: ", result)
                usage = int(result[0:len(result) - 1])
                if usage > 80:
                    result = danger_font_start_tag + result + danger_font_end_tag
                print("Usage ", str(usage))
            else:
                continue
        elif "uptime" in cmd:
            if "days" not in result:
                result = danger_font_start_tag + result + danger_font_end_tag
        elif "top" in cmd:
            if "load average: " in result:
                load_avg_str = result[result.index("load average:") + len("load average:"):len(result)]
                load_avg_arr = load_avg_str.split(",")
                load_avg_arr_size = len(load_avg_arr)
                load_avg_sum = 0.0
                for each_load in load_avg_arr:
                    print("each load: ", each_load)
                    print("each load len ", len(each_load))
                    if not each_load.isdecimal():
                        res = re.findall("\d*\.?\d+", each_load)
                        each_load = res[0]
                    load_val = float(each_load.strip())
                    load_avg_sum = load_avg_sum + load_val
                load_avg = (load_avg_sum / load_avg_arr_size) * 100
                if load_avg > 70:
                    load_avg_val = danger_font_start_tag + "load average: " + str(load_avg) + danger_font_end_tag
                else:
                    load_avg_val = "load average: " + str(load_avg)
            if "%Cpu" in result:
                cpu_val = ""
                cpu_line_arr = result.split(",")
                for cpu_line_val in cpu_line_arr:
                    if "id" in cpu_line_val:
                        cpu_val = cpu_line_val[0:cpu_line_val.index("id")]
                        print(cpu_val)
                        break
                if cpu_val != "":
                    print("cpu_val", cpu_val)
                    if not cpu_val.isdecimal():
                        print("Cpu val ", cpu_val)
                        cpu_val_res = re.findall("\d*\.?\d+", cpu_val)
                        print("cpu_utl_res ", cpu_val_res)
                        cpu_val = cpu_val_res[3]
                    cpu_final_utilization = 100 - float(cpu_val)
                    cpu_utilization = "CPU Utilization: " + str(cpu_final_utilization)
                    print(cpu_utilization)
        if "top" in cmd and (load_avg_val == "" or cpu_utilization == ""):
            continue
        elif "top" in cmd and (load_avg_val != "" or cpu_utilization != ""):
            result = load_avg_val + "<br>" + cpu_utilization
            top_loaded = True

        print("top_loaded :", top_loaded, "cpu_utilization: ", cpu_utilization, "load_avg_val: ", load_avg_val)
        if cmd_line_count == 0:
            body_text = body_text + "<tr><td rowspan=" + str(
                cmd_count) + ">" + host + "</td><td>" + org_cmd + "</td><td>" + str(result) + "</td></tr>"
        try:
            if cmd_line_count > 0:
                body_text = body_text + "<tr><td>" + org_cmd + "</td><td>" + str(result) + "</td></tr>"
            cmd_line_count = cmd_line_count + 1
            if "top" in cmd and top_loaded:
                break
        except:
            print("ERROR: for command ", cmd, "Result ", result)

main_body = header_text + body_text + "</table>"
# print(main_body)
smtp_host = "smtp.gmail.com"
smtp_port = 465
sender_email = "logerrors.notification@gmail.com"
sender_email_pass = "Welcome@IQZ"
to_email_addresses = "vijayalakshmi.v@iqzsystems.com,lavanya.r@iqzsystems.com"
cc_email_address = ""
bcc_email_address = ""
send_email_with_results(host, smtp_host, smtp_port, sender_email, sender_email_pass, to_email_addresses,
                        cc_email_address,
                        bcc_email_address, main_body)

