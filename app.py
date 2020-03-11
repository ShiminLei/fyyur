#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from datetime import datetime
import logging
from logging import Formatter, FileHandler
from forms import *
from models import db_setup, Venue, Show, Artist
from flask_moment import Moment


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db, migrate = db_setup(app)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

# used for formatting user time input


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

# home page route handler
@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

# venues page route handler
@app.route('/venues')
def venues():
    data = []

    venues = Venue.query.all()
    cities = set()
    for venue in venues:
        cities.add((venue.city, venue.state))

    for location in cities:
        data.append({
            "city": location[0],
            "state": location[1],
            "venues": []
        })

    for venue in venues:
        for entry in data:
            if venue.city == entry['city'] and venue.state == entry['state']:
                entry['venues'].append({
                    "id": venue.id,
                    "name": venue.name
                })

    return render_template('pages/venues.html', areas=data)

# venues search route handler
@app.route('/venues/search', methods=['POST'])
def search_venues():
    venues = Venue.query.filter(Venue.name.ilike('%' + request.form.get('search_term', '') + '%')).all()

    response = {
        "count": len(venues),
        "data": []
    }

    for venue in venues:
        response['data'].append({
            "id": venue.id,
            "name": venue.name
        })

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

# route handler for individual venue pages
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()

    if not venue:
        return render_template('errors/404.html')

    shows = Show.query.filter_by(venue_id=venue_id).all()
    upcoming_shows = []
    past_shows = []

    def get_show(show):
        return {
                "artist_id": show.artist_id,
                "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                "start_time": format_datetime(str(show.start_time))
            }

    for show in shows:
        if show.start_time >= datetime.now():
            upcoming_shows.append(get_show(show))
        else:
            past_shows.append(get_show(show))

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

# get the create venue form
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

# post handler for venue creation
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        venue = Venue(
            name = request.form['name'], 
            city = request.form['city'], 
            state = request.form['state'], 
            address = request.form['address'],
            phone = phone_validator(request.form['phone']), 
            genres = request.form.getlist('genres'), 
            facebook_link = request.form['facebook_link'],
            website = request.form['website'], 
            image_link = request.form['image_link'],
            seeking_talent = True if request.form['seeking_talent'] == 'Yes' else False,
            seeking_description = request.form['seeking_description']
            )

        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except ValidationError as e:
        # the wrong phone number
        db.session.rollback()
        flash('An error occurred.' + str(e))
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

# route handler for deleting venues
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.filter(Venue.id == venue_id).first()
        name = venue.name

        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + name + ' was successfully deleted.')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + name + ' could not be deleted.')
    finally:
        db.session.close()
    return None

#  Artists
#  ----------------------------------------------------------------

# route handler for artists overview page
@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)

# artist search route handler
@app.route('/artists/search', methods=['POST'])
def search_artists():
    artists = Artist.query.filter(Artist.name.ilike('%' + request.form.get('search_term', '') + '%')).all()

    response = {
        "count": len(artists),
        "data": []
    }

    for artist in artists:
        response['data'].append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

# route handler for individual artist pages
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()

    if not artist:
        return render_template('errors/404.html')

    shows = Show.query.filter_by(artist_id=artist_id).all()
    upcoming_shows = []
    past_shows = []

    def get_show(show):
        return {
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                    "start_time": format_datetime(str(show.start_time))
                }

    for show in shows:
        if show.start_time >= datetime.now():
            upcoming_shows.append(get_show(show))
        else:
            past_shows.append(get_show(show))

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------

# route handler for GET edit artist form
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm(request.form)

    artist = Artist.query.filter_by(id=artist_id).first()

    if not artist:
        return render_template('errors/404.html')

    artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }

    form.name.data = artist["name"]
    form.genres.data = artist["genres"]
    form.city.data = artist["city"]
    form.state.data = artist["state"]
    form.phone.data = artist["phone"]
    form.website.data = artist["website"]
    form.facebook_link.data = artist["facebook_link"]
    form.seeking_venue.data = 'Yes' if artist["seeking_venue"] else 'No'
    form.seeking_description.data = artist["seeking_description"]
    form.image_link.data = artist["image_link"]

    return render_template('forms/edit_artist.html', form=form, artist=artist)

# edit artist POST handler
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        form = ArtistForm(request.form)

        artist = Artist.query.filter_by(id=artist_id).first()

        if not artist:
            return render_template('errors/404.html')

        artist.name = form.name.data
        artist.genres = form.genres.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = phone_validator(form.phone.data)
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website = form.website.data
        artist.seeking_venue = True if form.seeking_venue.data == 'Yes' else False
        artist.seeking_description = form.seeking_description.data

        db.session.commit()

        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except ValidationError as e:
        db.session.rollback()
        flash('An error occurred.' + str(e))
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

# handler for venue edit GET
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm(request.form)

    venue = Venue.query.filter_by(id=venue_id).first()

    if not venue:
        return render_template('errors/404.html')

    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }

    form.name.data = venue["name"]
    form.genres.data = venue["genres"]
    form.address.data = venue["address"]
    form.city.data = venue["city"]
    form.state.data = venue["state"]
    form.phone.data = venue["phone"]
    form.website.data = venue["website"]
    form.facebook_link.data = venue["facebook_link"]
    form.seeking_talent.data = 'Yes' if venue["seeking_talent"] else 'No'
    form.seeking_description.data = venue["seeking_description"]
    form.image_link.data = venue["image_link"]

    return render_template('forms/edit_venue.html', form=form, venue=venue)

# venue edit POST handler
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        form = VenueForm(request.form)

        venue = Venue.query.filter_by(id=venue_id).first()

        if not venue:
            return render_template('errors/404.html')

        venue.name = form.name.data
        venue.genres = form.genres.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = phone_validator(form.phone.data)
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website.data
        venue.image_link = form.image_link.data
        venue.seeking_talent = True if form.seeking_talent.data == 'Yes' else False
        venue.seeking_description = form.seeking_description.data

        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except ValidationError as e:
        # for wrong phone number
        db.session.rollback()
        flash('An error occurred. ' + str(e))
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

# artist creation GET route handler
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

# artist creation POST handler
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        artist = Artist(
                        name=request.form['name'], 
                        city=request.form['city'], 
                        state=request.form['state'], 
                        phone=phone_validator(request.form['phone']),
                        genres=request.form.getlist('genres'), 
                        facebook_link=request.form['facebook_link'],
                        website=request.form['website'], 
                        image_link=request.form['image_link'],
                        seeking_venue=True if request.form['seeking_venue'] == 'Yes' else False,
                        seeking_description=request.form['seeking_description']
                        )

        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except ValidationError as e:
        db.session.rollback()
        flash('An error occurred. ' + str(e))
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

# delete artist route handler
@app.route('/artists/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.filter_by(id=artist_id).first()
        name = artist.name

        db.session.delete(artist)
        db.session.commit()
        flash('Artist ' + name + ' was successfully deleted.')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + name + ' could not be deleted.')
    finally:
        db.session.close()

    return None


#  Shows
#  ----------------------------------------------------------------

# route handler for shows page
@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
            "artist_id": show.artist_id,
            "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
            "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
            "start_time": format_datetime(str(show.start_time))
        })

    return render_template('pages/shows.html', shows=data)

# handler for rendering create shows page
@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

# POST handler for show create
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        show = Show(
            artist_id=request.form['artist_id'], 
            venue_id=request.form['venue_id'],
            start_time=request.form['start_time']
            )

        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

# error handlers

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
