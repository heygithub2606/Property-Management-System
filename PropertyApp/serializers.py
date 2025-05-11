from rest_framework import serializers
from .models import *


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['image']

class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, required=False)

    class Meta:
        model = Property
        fields = [
            'title', 'description', 'price', 'city', 
             'property_type', 'status', 'landlord_email', 
            'phone_no', 'images'
        ]

    def create(self, validated_data):
        # Pop the images data from validated_data if present
        images_data = validated_data.pop('images', [])

        # Create the Property instance
        property_instance = Property.objects.create(**validated_data)

        # If images data exists, create PropertyImage instances
        if images_data:
            for image_data in images_data:
                PropertyImage.objects.create(property=property_instance, **image_data)

        return property_instance

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)

        # Update the fields on the Property instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle images if images_data is provided
        if images_data is not None:
            # Optionally delete existing images if new images are provided
            instance.images.all().delete()  
            for image_data in images_data:
                PropertyImage.objects.create(property=instance, **image_data)

        return instance
    