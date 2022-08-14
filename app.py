import datetime
import json
from flask import Flask, abort, redirect
import sys
from flask_restful import Api, Resource, reqparse, fields, inputs, marshal_with
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
api = Api(app)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///etc.db.sqlite'
parser = reqparse.RequestParser()


# creates a declarative table model and adds it
class Event(db.Model):
    __tablename__ = 'Events'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(30), nullable=False)
    date = db.Column(db.DateTime, nullable=False)


event_fields = {
    'id': fields.Integer(),
    'event': fields.String(),
    'date': fields.DateTime()
}


# init the database
db.create_all()


class TodayEventsResource(Resource):
    @marshal_with(event_fields)
    def get(self):
        return Event.query.filter(Event.date == datetime.date.today()).all()


class EventById(Resource):
    @marshal_with(event_fields)
    def get(self, event_id):
        result = Event.query.filter(Event.id == event_id).all()
        if not result:
            abort(404, "The event does not exist!")
        return result


class EventsByRange(Resource):
    @marshal_with(event_fields)
    def get(self):
        parser.add_argument('start_time', type=inputs.date, required=False, location='args')
        parser.add_argument('end_time', type=inputs.date, required=False, location='args')
        args = parser.parse_args()
        parser.remove_argument('start_time')
        parser.remove_argument('end_time')
        result = Event.query.all()
        # if not result:
        #     # print("Returning events in a range")
        #     abort(404, "No events exist!")
        if args.get('start_time') and args.get('end_time'):
            result = Event.query.filter(Event.date.between(args['start_time'], args['end_time'])).all()

        return result

    def post(self):
        parser.add_argument('event', type=str, help="The event name is required!", required=True)
        parser.add_argument('date', type=inputs.date, help="The event date with the correct format is required! The correct format is YYYY-MM-DD!", required=True)
        args = parser.parse_args()
        parser.remove_argument('event')
        parser.remove_argument('date')
        db.session.add(Event(event=args['event'], date=args['date'].date()))
        db.session.commit()

        return {
            "message": "The event has been added!",
            "event": args['event'],
            "date": str(args['date'].date())
        }


class DeleteEvent(Resource):
    def delete(self, event_id):
        result = Event.query.filter(Event.id == event_id).first()
        if not result:
            abort(404, "The event does not exist!")
        db.session.delete(result)
        db.session.commit()
        return {
            "message": "The event has been deleted!"
        }


api.add_resource(EventsByRange, '/event')
api.add_resource(TodayEventsResource, '/event/today')
api.add_resource(EventById, '/event/<int:event_id>')
api.add_resource(DeleteEvent, '/event/<int:event_id>')


# do not change the way you run the program
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(debug=True, host=arg_host, port=arg_port)
    else:
        app.run(debug=True)
