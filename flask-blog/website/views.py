from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Post, User, Comment, Like, Note
from . import db
import json

views = Blueprint("views", __name__)


@views.route("/")
@views.route("/home")
@login_required
def home():
    posts = Post.query.all()
    return render_template("home.html", user=current_user, posts=posts)


@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == "POST":
        text = request.form.get('text')

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(text=text, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('create_post.html', user=current_user)


@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.author and current_user.role != "admin":
        print(f"Current user id: {current_user.id}, Post author id: {post.author}, Current user role: {type( current_user.role)}")
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('views.home'))


@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    posts = user.posts
    return render_template("posts.html", user=current_user, posts=posts, username=username)


@views.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(
                text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('views.home'))


@views.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author and current_user.role != "admin":
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('views.home'))


@views.route("/like-post/<post_id>", methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(
        author=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exist.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})


@views.route("/profile")
@login_required
def profile():
    return render_template("profile.html",user=current_user)



@views.route("/delete-profile/<user_id>", methods=['POST'])
@login_required
def delete_profile(user_id):
    user = User.query.get(user_id)

    if not user:
        flash("User not found.", category='error')
    elif current_user.id != user.id and current_user.role != "admin":
        flash('You do not have permission to delete this user.', category='error')
    else:
        # Delete user's posts, comments, and likes
        for post in user.posts:
            # Delete post's comments
            Comment.query.filter_by(post_id=post.id).delete()
            # Delete post's likes
            Like.query.filter_by(post_id=post.id).delete()

            # Delete post
            db.session.delete(post)

        # Delete user's comments and likes
        Comment.query.filter_by(author=user.id).delete()
        Like.query.filter_by(author=user.id).delete()

        db.session.delete(user)
        db.session.commit()
        flash('User and associated data deleted.', category='success')

    return redirect(url_for('views.home'))

@views.route("/change-password")
@login_required
def change_password():
    return render_template("change_password.html", user=current_user)

from werkzeug.security import check_password_hash, generate_password_hash

@views.route("/process-password-change", methods=['POST'])
@login_required
def process_password_change():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password_hash(current_user.password, current_password):
        flash('Incorrect current password.', category='error')
    elif new_password != confirm_password:
        flash('New password and confirm password do not match.', category='error')
    else:
        # Update user's password in the database
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password successfully changed.', category='success')

    return redirect(url_for('views.change_password'))


@views.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    if request.method == 'POST':
        note = request.form.get('note')  # Gets the note from the HTML

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)  # providing the schema for the note
            db.session.add(new_note)  # adding the note to the database
            db.session.commit()
            flash('Note added!', category='success')
            return redirect(url_for('views.notes'))

    return render_template("notes.html", user=current_user, notes=current_user.notes)




@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})