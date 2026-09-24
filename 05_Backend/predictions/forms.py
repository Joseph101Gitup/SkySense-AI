"""
Forms for image upload and prediction submission.
"""

from PIL import Image
from django import forms
from django.conf import settings


class ImagePredictionForm(forms.Form):
    """
    Form for uploading a sky/cloud image for rainfall prediction.
    """
    image = forms.ImageField(
        label="Cloud Sky Image",
        required=True,
        widget=forms.FileInput(attrs={
            'id': 'image-file-input',
            'class': 'hidden',
            'accept': '.jpg,.jpeg,.png,image/jpeg,image/png',
        })
    )
    notes = forms.CharField(
        label="Observation Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Add field context, location, or visual notes...',
            'class': 'w-full px-4 py-2.5 bg-slate-900/60 border border-slate-700/80 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500/50 text-sm transition',
        })
    )

    def clean_image(self):
        img = self.cleaned_data.get('image')
        if img:
            # 1. File size validation
            if img.size > settings.MAX_UPLOAD_SIZE:
                max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
                raise forms.ValidationError(f"File size exceeds maximum allowed limit of {max_mb:.0f} MB.")

            # 2. Extension validation
            ext = img.name.split('.')[-1].lower() if '.' in img.name else ''
            if f".{ext}" not in settings.ALLOWED_IMAGE_EXTENSIONS:
                raise forms.ValidationError(
                    f"Unsupported format '.{ext}'. Supported formats: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}."
                )

            # 3. MIME type validation (if provided by client header)
            if hasattr(img, 'content_type') and img.content_type:
                if img.content_type not in settings.ALLOWED_IMAGE_MIME_TYPES:
                    raise forms.ValidationError(
                        f"Unsupported MIME type '{img.content_type}'. Allowed MIME types: {', '.join(settings.ALLOWED_IMAGE_MIME_TYPES)}."
                    )

            # 4. Deep binary verification with PIL
            try:
                img.seek(0)
                with Image.open(img) as pil_img:
                    pil_img.verify()
                    if pil_img.format not in ['JPEG', 'PNG']:
                        raise forms.ValidationError(
                            f"Image format '{pil_img.format}' is not supported. Only JPEG and PNG are allowed."
                        )
                img.seek(0)
            except forms.ValidationError:
                raise
            except Exception as e:
                raise forms.ValidationError(f"Uploaded file is corrupted or not a valid image: {e}")

        return img
