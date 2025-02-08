from rest_framework import serializers
from . models import Task
from users.models import CustomUser

class TaskSerializer(serializers.ModelSerializer):
    created_by_username = serializers.SerializerMethodField(read_only=True)
    assigned_to_username = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_by','created_at','updated_at']

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None
    
    def get_assigned_to_username(self, obj):
        return obj.assigned_to.username
    

    def validate(self, data):
        
        request = self.context.get('request')
        user = request.user if request else None

        if not user:
            raise serializers.ValidationError("Authentication required")

    
        if user.role not in ['superadmin', 'admin'] and 'assigned_to' in data:
            if data['assigned_to'] != user:
                raise serializers.ValidationError("You can only assign tasks to yourself")

        
        if data.get('status') == 'completed':  
            if not data.get('completion_report'):
                raise serializers.ValidationError({"completion_report": "Completion report is required when marking task as completed."})
            if data.get('worked_hours') is None:
                raise serializers.ValidationError({"worked_hours": "Worked hours must be provided when marking task as completed."})
        
        return data
    
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)
