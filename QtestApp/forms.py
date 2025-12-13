from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    # Add a specific validation for the 'agree_to_terms' checkbox
    agree_to_terms = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must agree to the terms and conditions.'}
    )

    class Meta:
        model = ContactMessage
        # Specify the fields to include in the form
        fields = ['name', 'email', 'subject', 'message', 'agree_to_terms']
        # Customize the labels to match the image
        labels = {
            'name': 'Your Name (required)',
            'email': 'Your Email (required)',
            'subject': 'Subject',
            'message': 'Your Message',
            'agree_to_terms': 'I agree to terms and conditions.'
        }
        # Add widgets to control the HTML rendering of the fields
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'e.g., yourname@example.com'}),
            'subject': forms.TextInput(attrs={'placeholder': 'What is the subject?'}),
            'message': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Write your message here...'}),
        }