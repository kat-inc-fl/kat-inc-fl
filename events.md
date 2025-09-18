---
layout: page
title: Events
permalink: /events/
---
# Upcoming & Past Events

{% for post in site.posts %}
- [ {{post.date | date: "%-d %b %Y" }} - {{ post.title }}]({{ post.url }})
{% endfor %}
