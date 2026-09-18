from django import forms

from .models import DonorProfile, DonationHistory


class DonorProfileForm(forms.ModelForm):

    class Meta:

        model = DonorProfile

        fields = [
            "blood_group",
            "latitude",
            "longitude",
            "address",
            "is_available",
        ]

        widgets = {

            "blood_group": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "latitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "any",
                    "placeholder": "Latitude",
                    "id": "id_latitude",
                }
            ),

            "longitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "any",
                    "placeholder": "Longitude",
                    "id": "id_longitude",
                }
            ),

            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your area/address",
                }
            ),

            "is_available": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),

        }


class DonationHistoryForm(forms.ModelForm):

    class Meta:

        model = DonationHistory

        fields = [
            "donation_date",
            "hospital_name",
            "donation_type",
        ]

        widgets = {

            "donation_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "hospital_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Hospital/Blood bank name",
                }
            ),

            "donation_type": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Whole Blood",
                }
            ),

        }