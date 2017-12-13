# -*- coding: utf-8 -*-
import attr
import random
import itertools
from cached_property import cached_property

from navmazing import NavigateToAttribute, NavigateToSibling
from wrapanapi.containers.project import Project as ApiProject

from cfme.common import WidgetasticTaggable, TagPageView
from cfme.containers.provider import (Labelable, ContainerObjectAllBaseView,
                                      ContainerObjectDetailsBaseView)
from cfme.modeling.base import BaseCollection, BaseEntity
from cfme.utils.appliance.implementations.ui import CFMENavigateStep, navigator


class ProjectAllView(ContainerObjectAllBaseView):
    SUMMARY_TEXT = "Projects"


class ProjectDetailsView(ContainerObjectDetailsBaseView):
    pass


@attr.s
class Project(BaseEntity, WidgetasticTaggable, Labelable):

    PLURAL = 'Projects'
    all_view = ProjectAllView
    details_view = ProjectDetailsView

    name = attr.ib()
    provider = attr.ib()

    @cached_property
    def mgmt(self):
        return ApiProject(self.provider.mgmt, self.name)

    @classmethod
    def get_random_instances(cls, provider, count=1, appliance=None):
        """Generating random instances."""
        project_list = provider.mgmt.list_project()
        random.shuffle(project_list)
        return [cls(obj.name, provider, appliance=appliance)
                for obj in itertools.islice(project_list, count)]


@attr.s
class ProjectCollection(BaseCollection):
    """Collection object for :py:class:`Project`."""

    ENTITY = Project


@navigator.register(ProjectCollection, 'All')
class All(CFMENavigateStep):
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')
    VIEW = ProjectAllView

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Containers', 'Projects')

    def resetter(self):
        # Reset view and selection
        self.view.toolbar.view_selector.select("List View")
        if self.view.paginator.is_displayed:
            self.view.paginator.reset_selection()


@navigator.register(Project, 'Details')
class Details(CFMENavigateStep):
    VIEW = ProjectDetailsView
    prerequisite = NavigateToAttribute('parent', 'All')

    def step(self):
        self.prerequisite_view.entities.get_entity(name=self.obj.name).click()


@navigator.register(Project, 'EditTags')
class ImageRegistryEditTags(CFMENavigateStep):
    VIEW = TagPageView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.toolbar.policy.item_select('Edit Tags')
