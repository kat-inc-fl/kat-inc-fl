---
layout: page
title: Contact
permalink: /contact/
---
# Contact Us

We’d love to hear from you! Please fill out the form below:

<form action="https://formspree.io/f/mnnbeqjb" method="POST" class="contact-form">
  <label for="name">Name:</label>
  <input type="text" id="name" name="name" placeholder="Your name" required>

  <label for="email">Email:</label>
  <input type="email" id="email" name="_replyto" placeholder="you@example.com" required>

  <label for="message">Message:</label>
  <textarea id="message" name="message" rows="6" placeholder="Your message..." required></textarea>

  <input type="submit" value="Send">
</form>

## Follow Us

<div class="social-icons">
  <a href="https://www.facebook.com/koreanadopteestogether" target="_blank" aria-label="Facebook">
    <i class="fab fa-facebook-square fa-2x"></i>
  </a>
  <a href="https://www.instagram.com/koreanadopteestogether/" target="_blank" aria-label="Instagram">
    <i class="fab fa-instagram fa-2x"></i>
  </a>
</div>

<style>
.contact-form {
  max-width: 600px;
  margin: 2em auto;
  padding: 1.5em;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}
.contact-form label {
  font-weight: bold;
  margin-top: 1em;
}
.contact-form input[type="text"],
.contact-form input[type="email"],
.contact-form textarea {
  width: 100%;
  padding: 0.75em;
  margin-top: 0.5em;
  margin-bottom: 1em;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 1em;
}
.contact-form input[type="submit"] {
  width: 100%;
  padding: 0.75em;
  background-color: #0073e6;
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 1.1em;
  cursor: pointer;
}
.contact-form input[type="submit"]:hover {
  background-color: #005bb5;
}
.social-icons {
  display: flex;
  gap: 1em;
  margin-top: 1em;
}
.social-icons a {
  color: #333;
  transition: color 0.3s;
}
.social-icons a:hover {
  color: #0073e6;
}
</style>
