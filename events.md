---
layout: page
title: Events
permalink: /events/
---
# Upcoming & Past Events

{% for post in site.posts %}
- [ {{post.date | date_to_string: "US" }} - {{ post.title }}]({{ post.url }})
{% endfor %}
