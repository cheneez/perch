from django import forms

from .models import Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        # owner/created_at are set by the system
        exclude = ["owner", "created_at", "verified", "avg_rating", "image_count", "video_count", "latitude", "longitude"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Cozy 2BR near campus"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe the space, amenities, and anything tenants should know.",
                }
            ),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": "123 Main St, City, ST"}),
            "price_monthly": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "estimated_utilities_cost": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "security_deposit": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "broker_fee": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "application_fee": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "total_upfront_cost": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "bedrooms": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 1}),
            "bathrooms": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 1}),
            "distance_miles": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.1"}),
            "room_type": forms.Select(attrs={"class": "form-select"}),
            "lease_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "lease_start": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "lease_end": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "utilities_included": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "parking_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "pets_allowed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "stairs": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "shared_space": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_laundry": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_ac_heat": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

