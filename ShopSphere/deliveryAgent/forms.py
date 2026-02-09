from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Agent

class AgentRegistrationForm(UserCreationForm):
    mobile = forms.CharField(max_length=15, required=True)
    license_number = forms.CharField(max_length=50, required=True)
    company_name = forms.CharField(max_length=100, required=True)
    vehicle_type = forms.ChoiceField(choices=[('bike', 'Bike'), ('van', 'Van'), ('truck', 'Truck')])

    class Meta(UserCreationForm.Meta):
        model = Agent
        fields = UserCreationForm.Meta.fields + (
            'email', 'mobile', 'license_number', 'vehicle_type', 'company_name'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full p-5 bg-gray-50 border-2 border-gray-100 rounded-[2rem] font-bold tracking-wide focus:border-[#5D56D1] outline-none transition-all'
            })

        self.fields['username'].widget.attrs.update({
            'class': 'custom-input-class' 
        })