from django import forms

from .models import BloodRequest


class BloodRequestForm(forms.ModelForm):

    class Meta:

        model = BloodRequest

        fields = [
            "blood_group",
            "hospital_name",
            "hospital_address",
            "latitude",
            "longitude",
            "units_required",
            "urgency",
            "radius_km",
            "description",
            "expires_at",
        ]

        widgets = {

            "blood_group": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "hospital_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter hospital name",
                }
            ),

            "hospital_address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter hospital address",
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

            "units_required": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "20",
                }
            ),

            "urgency": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "radius_km": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.5",
                    "min": "1",
                    "max": "100",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": "4",
                    "placeholder": "Additional information about the blood requirement",
                }
            ),

            "expires_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),

        }

    def clean_units_required(self):

        units = self.cleaned_data["units_required"]

        if units < 1:
            raise forms.ValidationError(
                "At least one unit is required."
            )

        return units

    def clean_radius_km(self):

        radius = self.cleaned_data["radius_km"]

        if radius <= 0:
            raise forms.ValidationError(
                "Search radius must be greater than zero."
            )

        return radius

    def clean_latitude(self):

        latitude = self.cleaned_data["latitude"]

        if latitude < -90 or latitude > 90:
            raise forms.ValidationError(
                "Latitude must be between -90 and 90."
            )

        return latitude

    def clean_longitude(self):

        longitude = self.cleaned_data["longitude"]

        if longitude < -180 or longitude > 180:
            raise forms.ValidationError(
                "Longitude must be between -180 and 180."
            )

        return longitude