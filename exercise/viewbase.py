from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cached.content import NoSuchContent
from course.viewbase import CourseModuleMixin
from lib.viewbase import BaseTemplateView
from authorization.permissions import ACCESS
from .permissions import (
    ExerciseVisiblePermission,
    BaseExerciseAssistantPermission,
    SubmissionVisiblePermission,
)
from .models import (
    LearningObject,
    BaseExercise,
    Submission,
)


class ExerciseBaseMixin(object):
    exercise_kw = "exercise_path"
    exercise_permission_classes = (
        ExerciseVisiblePermission,
    )

    def get_permissions(self):
        perms = super().get_permissions()
        perms.extend((Perm() for Perm in self.exercise_permission_classes))
        return perms

    # get_exercise_object

    def get_resource_objects(self):
        super().get_resource_objects()
        self.exercise = self.get_exercise_object()
        previous_entry, current_entry, next_entry = self.content.find(self.exercise)
        self.now = timezone.now()
        self.previous = previous_entry
        self.current = current_entry
        self.next = next_entry
        self.breadcrumb = self.content.breadcrumb(self.exercise)
        self.note("exercise", "now", "previous", "current", "next", "breadcrumb")


class ExerciseMixin(ExerciseBaseMixin, CourseModuleMixin):
    exercise_permission_classes = ExerciseBaseMixin.exercise_permission_classes + (
        BaseExerciseAssistantPermission,
    )

    def get_exercise_object(self):
        try:
            exercise_id = self.content.find_path(
                self.module.id,
                self.kwargs[self.exercise_kw]
            )
            return LearningObject.objects.get(id=exercise_id).as_leaf_class()
        except (NoSuchContent, LearningObject.DoesNotExist):
            raise Http404("Learning object not found")


class ExerciseBaseView(ExerciseMixin, BaseTemplateView):
    pass


class SubmissionBaseMixin(object):
    submission_kw = "submission_id"
    submission_permission_classes = (
        SubmissionVisiblePermission,
    )

    def get_permissions(self):
        perms = super().get_permissions()
        perms.extend((Perm() for Perm in self.submission_permission_classes))
        return perms

    # get_submission_object

    def get_resource_objects(self):
        super().get_resource_objects()
        self.submission = self.get_submission_object()
        self.note("submission")


class SubmissionMixin(SubmissionBaseMixin, ExerciseMixin):
    def get_submission_object(self):
        return get_object_or_404(
            Submission,
            id=self.kwargs[self.submission_kw],
            exercise=self.exercise
        )


class SubmissionBaseView(SubmissionMixin, BaseTemplateView):
    pass
