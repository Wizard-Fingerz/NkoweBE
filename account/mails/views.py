# views.py
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from .models import MailTemplate
from .serializers import MailTemplateSerializer
from django.core.mail import send_mass_mail

class SendMassEmailView(APIView):
    # Was fully open (no permission_classes) — anyone on the internet could
    # trigger a mass email blast to any list of addresses they supplied,
    # using this server's mail credentials. Restricted to staff/superusers.
    permission_classes = [IsAdminUser]

    def post(self, request):
        mail_template_id = request.data.get('mail_template_id')
        emails = request.data.get('emails')

        if not mail_template_id or not emails:
            return Response({'error': 'Mail template ID and emails are required'}, status=400)

        try:
            mail_template = MailTemplate.objects.get(id=mail_template_id)
        except MailTemplate.DoesNotExist:
            return Response({'error': 'Mail template not found'}, status=404)

        subject = mail_template.subject
        body = mail_template.body
        messages = [(subject, body, 'from@example.com', [email]) for email in emails]

        send_mass_mail(messages, fail_silently=False)
        return Response({'message': 'Mass email sent successfully'})