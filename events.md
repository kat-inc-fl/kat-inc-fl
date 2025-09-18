---
layout: page
title: Events
permalink: /events/
---
# Upcoming & Past Events

{% for post in site.posts %}
- [{{ post.title }}]({{ post.url }}) — {{ post.date | date: "%B %-d, %Y" }}
{% endfor %}
