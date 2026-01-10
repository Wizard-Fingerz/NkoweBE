from rest_framework import serializers, viewsets, generics, permissions
from .models import Assignment, StudentAssignment
from .serializers import AssignmentSerializer, StudentAssignmentSerializer, StudentAssignmentSerializer

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer


class StudentAssignmentCreateUpdateView(generics.CreateAPIView, generics.UpdateAPIView):
    serializer_class = StudentAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudentAssignment.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        assignment_id = self.request.data.get("assignment")
        if not assignment_id:
            raise serializers.ValidationError({"assignment": "This field is required."})

        try:
            assignment = Assignment.objects.get(id=assignment_id)
        except Assignment.DoesNotExist:
            raise serializers.ValidationError({"assignment": "Invalid assignment ID."})

        serializer.save(student=self.request.user, assignment=assignment)

    def perform_update(self, serializer):
        if not serializer.instance.is_draft:
            raise PermissionDenied("This assignment has already been submitted.")
        serializer.save()


class StudentAssignmentDetailView(generics.RetrieveAPIView):
    serializer_class = StudentAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudentAssignment.objects.filter(student=self.request.user)


class AllStudentAssignmentsView(generics.ListAPIView):
    serializer_class = StudentAssignmentSerializer
    queryset = StudentAssignment.objects.all()
    permission_classes = [permissions.IsAdminUser]
