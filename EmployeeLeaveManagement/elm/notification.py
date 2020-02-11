rom django.core.mail import EmailMultiAlternatives


def send_email(subject, text_content, html_content, to):
    """
    This function will send email notification
    :param subject:
    :param text_content:
    :param html_content:
    :param to:
    :return:
    """
    from_email = 'lemoncore@lemonsky.tv'
    footer = """<div>
                </br>
                </br>
                </br>
                </br>
                <h5>Do not reply to this email. This is automated email notification from LemonCORE.</h5>
                </br>
                <img src="http://lemonsky.in:8080/img/lemoncore.png" style="width:250px;height:53px;>
                <div style="font-size: 13px; font-family: Tahoma, Helvetica, sans-serif;"><br></div>
                <div style="font-size: 13px; font-family: Tahoma, Helvetica, sans-serif;"><br></div>
                <div style="font-size: 13px; font-family: Tahoma, Helvetica, sans-serif;"><br></div>
                <div style="font-size: 13px; font-family: Tahoma, Helvetica, sans-serif;"><span style="color: rgb(153, 153, 153); font-family: tahoma, sans-serif; font-size: x-small; background-color: rgb(255, 255, 255);">This message and any attachment(s) is intended only for the use of the addressee(s) and may contain information that is PRIVILEGED and CONFIDENTIAL. If you are not the intended addressee(s), you are hereby notified that any use, distribution, disclosure or copying of this communication is strictly prohibited. If you have received this communication in error, please erase all copies of the message and its attachment(s) and notify the sender immediately.</span></div>&nbsp;</div>
                </div>
                """
    email_body = html_content + '\n' + footer
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(email_body, "text/html")
    msg.send()
