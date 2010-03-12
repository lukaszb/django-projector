from django.contrib.syndication.feeds import Feed

from projector.models import Project

class LatestProjectsFeed(Feed):
    title = "Latest projects"
    link = "/projects/"
    description = "Updates on additions to projects."

    def items(self):
        return Project.objects\
            .order_by('-created_at')\
            .filter(public=True)\
            [:5] # Limiting query

