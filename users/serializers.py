from rest_framework import serializers
from . models import CustomUser
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls,user):
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        token["role"] = user.role
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser
        return token

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,required=True,validators =[validate_password])
    confirm_password = serializers.CharField(write_only=True,required=True)

    class Meta:
        model = CustomUser
        fields = ['id','username','email','role','password','confirm_password']
        extra_kwargs = {
            'username':{'required':True},
            'email':{'required':True},
            'role':{'required':False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password":"Password fields didn't match."})
        
        if 'email' in attrs:
            email = attrs['email']
            if CustomUser.objects.filter(email=email).exists():
                raise serializers.ValidationError({"email":"Email already exists"})
            
        request = self.context.get('request')
        if request and request.user and not request.user.is_anonymous:
            if 'role' in attrs:
                if attrs['role'] == 'superadmin' and not request.user.is_superadmin:
                    raise serializers.ValidationError(
                        {"role":"Only superadmin can create superadmin users"}
                    )
                if attrs['role'] == 'admin' and not request.user.is_admin:
                    raise serializers.ValidationError(
                        {"role":"Only admin or superadmin can create admin users"}
                    )
                
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data['password'] = make_password(validated_data['password'])

        if 'role' not in validated_data:
            validated_data['role'] = 'user'

        return CustomUser.objects.create(**validated_data)
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username','email','role']
        extra_kwargs = {
            'username':{'required':False},
            'email':{'required':False},
            'role':{'required':False}
        }

    def validate_email(self,value):
        instance = self.instance
        if CustomUser.objects.exclude(pk=instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate(self,attrs):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        if 'role' in attrs:
            if attrs['role'] == 'superadmin' and not request.user.is_superadmin:
                raise serializers.ValidationError(
                    {"role":"Only superadmin can assign superadmin role"}
                )
            
            if attrs['role'] == 'admin' and not request.user.is_admin:
                raise serializers.ValidationError(
                    {"role":"Only admin or superadmin can assign admin role"}
                )
        return attrs
        

    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        if user.role != 'superadmin':
            validated_data.pop('role',None)
        
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    


