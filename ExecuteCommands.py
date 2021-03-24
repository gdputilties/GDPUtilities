import os
import re
import smtplib
import socket
import ssl
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def execute_commands(commands):
    command_list = commands.split(",")
    cmd_count = len(command_list)
    body_text = ""
    top_loaded = False
    load_avg_val = ""
    cpu_utilization = ""
    command_line_count = 0
    danger_font_start = "<font color='red'>"
    danger_font_end = "</font>"
    header_text = "<table border=1><tr bgcolor=yellow><th>Host</th><th>Monitoring Parameter</th><th>Result</th></tr>"
    for cmd in command_list:
        print("Executing the command: ", cmd)
        org_cmd = cmd
        if "top" in cmd:
            cmd = cmd + " -n 1"
        stream = os.popen(cmd)
        output = stream.readlines()
        final_result = ""

        if len(output) > 0:
            for result in output:
                final_result = result
                if "df" in cmd:
                    if final_result != "":
                        #final_result = final_result + "<br>" + result
                        final_result = result
                    else:
                        final_result = result
                elif "uptime" in cmd:
                    if "days" not in result:
                        final_result = danger_font_start + result + danger_font_end
                elif "top" in cmd:
                    if "load average: " in result:
                        load_avg_str = result[result.index("load average:") + len("load average:"):len(result)]
                        print("load_avg_str: ", load_avg_str)
                        load_avg_arr = load_avg_str.split(",")
                        print("load_avg_arr: ", load_avg_arr)
                        load_avg_arr_size = len(load_avg_arr)
                        print("load_avg_arr_size: ", load_avg_arr_size)
                        load_avg_sum = 0.0
                        for each_load in load_avg_arr:
                            print("each_load : ", each_load)
                            print("each load length: ", len(each_load))
                            if not each_load.isdecimal():
                                res = re.findall("\d*\.?\d+", each_load)
                                each_load = res[0]
                                load_val = float(each_load.strip())
                                load_avg_sum = load_avg_sum + load_val
                        load_avg = (load_avg_sum / load_avg_arr_size) * 100
                        if load_avg > 70:
                            load_avg_val = danger_font_start + "load average: " + str(load_avg) + danger_font_end
                        else:
                            load_avg_val = "load average: " + str(load_avg)
                    if "Cpu" in result:
                        print("CPU Line: ", result)
                        cpu_val = ""
                        cpu_line_arr = result.split(",")
                        for cpu_line_val in cpu_line_arr:
                            if "id" in cpu_line_val:
                                cpu_val = cpu_line_val[0:cpu_line_val.index("id")]
                                print(cpu_val)
                                break
                        if cpu_val != "":
                            print("CPU VAL: ", cpu_val)
                            if not cpu_val.isdecimal():
                                print("Cpu val ", cpu_val)
                                cpu_val_res = re.findall("\d*\.?\d+", cpu_val)
                                print("cpu_utl_res ", cpu_val_res)
                                cpu_val = cpu_val_res[3]
                            cpu_final_utilization = 100 - float(cpu_val)
                            cpu_utilization = "CPU Utilization: " + str(cpu_final_utilization)
                            print("CPU Utilization:  ", cpu_utilization)

                    if load_avg_val == "" or cpu_utilization == "":
                        continue
                    elif load_avg_val != "" and cpu_utilization != "":
                        final_result = load_avg_val + "<br>" + cpu_utilization
                        top_loaded = True
                        break
        print("top_loaded :", top_loaded, "cpu_utilization: ", cpu_utilization, "load_avg_val: ", load_avg_val)
        if command_line_count == 0:
            body_text = body_text + "<tr><td rowspan=" + str(
                cmd_count) + ">" + host + "</td><td>" + org_cmd + "</td><td>" + str(final_result) + "</td></tr>"
            command_line_count = command_line_count + 1
        else:
            try:
                body_text = body_text + "<tr><td>" + org_cmd + "</td><td>" + str(final_result) + "</td></tr>"
                cmd_line_count = cmd_line_count + 1
            except:
                print("ERROR: for command ", cmd, "Result ", final_result)
    commands_op = header_text + body_text + "</table>"
    return commands_op


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
    recepients = to_emails + cc_emails + bcc_emails
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
            server.sendmail(sender_email, recepients, mail_body)
            print("Email sent successfully")
        except Exception:
            print("Unable to send email")
            traceback.print_exc()
        server.quit()


commands_to_execute = "date,hostname,uptime,df -hP /boot,df -hP /home,df -hP /root,top"
smtp_host = "smtp.gmail.com"
smtp_port = 465
sender_email = "logerrors.notification@gmail.com"
sender_email_pass = "Welcome@IQZ"
to_email_addresses = "vijayalakshmi.v@iqzsystems.com"
cc_email_address = ""
bcc_email_address = ""
host = socket.gethostname()
commands_output = execute_commands(commands_to_execute)
print(commands_output)
if commands_output != "":
    send_email_with_results(host, smtp_host, smtp_port, sender_email, sender_email_pass, to_email_addresses,
                            cc_email_address,
                            bcc_email_address, commands_output)

