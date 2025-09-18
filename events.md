---
layout: page
title: Events
permalink: /events/
---
# Upcoming & Past Events

{% for post in site.posts %}
- [ {{post.date | date: "%b %-d, %Y" }} - {{ post.title }}]({{ post.url }})
{% endfor %}
