from datetime import timedelta

import grpc
import pytest
from google.protobuf import wrappers_pb2

from couchers import errors
from couchers.db import session_scope
from couchers.utils import Timestamp_from_datetime, now, to_aware_datetime
from pb import events_pb2
from tests.test_communities import create_community
from tests.test_fixtures import db, events_session, generate_user, testconfig


@pytest.fixture(autouse=True)
def _(testconfig):
    pass


def test_CreateEvent(db):
    # test cases:
    # can create event
    # cannot create event with missing details
    # can create online event
    # can create in person event
    # can't create event that starts in the past
    # can create in different timezones

    # event creator
    user1, token1 = generate_user()
    # community moderator
    user2, token2 = generate_user()
    # third party
    user3, token3 = generate_user()

    with session_scope() as session:
        c_id = create_community(session, 0, 2, "Community", [user2], [], None).id

    time_before = now()
    start_time = now() + timedelta(hours=2)
    end_time = start_time + timedelta(hours=3)

    with events_session(token1) as api:
        # in person event
        res = api.CreateEvent(
            events_pb2.CreateEventReq(
                title="Dummy Title",
                content="Dummy content.",
                photo_key=None,
                location=events_pb2.Coordinate(
                    lat=0.1,
                    lng=0.2,
                ),
                address="Near Null Island",
                is_online_only=False,
                link=None,
                start_time=Timestamp_from_datetime(start_time),
                end_time=Timestamp_from_datetime(end_time),
                timezone="UTC",
            )
        )

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert not res.is_online_only
        assert not res.link
        assert res.location.lat == 0.1
        assert res.location.lng == 0.2
        assert res.address == "Near Null Island"
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_GOING
        assert res.organizer
        assert res.subscriber
        assert res.going_count == 1
        assert res.maybe_count == 0
        assert res.organizer_count == 1
        assert res.subscriber_count == 1
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert res.can_edit
        assert not res.can_moderate

        event_id = res.event_id

    with events_session(token2) as api:
        res = api.GetEvent(events_pb2.GetEventReq(event_id=event_id))

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert not res.is_online_only
        assert not res.link
        assert res.location.lat == 0.1
        assert res.location.lng == 0.2
        assert res.address == "Near Null Island"
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_NOT_GOING
        assert not res.organizer
        assert not res.subscriber
        assert res.going_count == 1
        assert res.maybe_count == 0
        assert res.organizer_count == 1
        assert res.subscriber_count == 1
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert not res.can_edit
        assert res.can_moderate

    with events_session(token3) as api:
        res = api.GetEvent(events_pb2.GetEventReq(event_id=event_id))

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert not res.is_online_only
        assert not res.link
        assert res.location.lat == 0.1
        assert res.location.lng == 0.2
        assert res.address == "Near Null Island"
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_NOT_GOING
        assert not res.organizer
        assert not res.subscriber
        assert res.going_count == 1
        assert res.maybe_count == 0
        assert res.organizer_count == 1
        assert res.subscriber_count == 1
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert not res.can_edit
        assert not res.can_moderate

    with events_session(token1) as api:
        # online only event
        res = api.CreateEvent(
            events_pb2.CreateEventReq(
                title="Dummy Title",
                content="Dummy content.",
                photo_key=None,
                location=None,
                address=None,
                is_online_only=True,
                parent_community_id=c_id,
                link="https://app.couchers.org/meet/",
                start_time=Timestamp_from_datetime(start_time),
                end_time=Timestamp_from_datetime(end_time),
                timezone="UTC",
            )
        )

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert res.is_online_only
        assert res.link == "https://app.couchers.org/meet/"
        assert not res.location.lat
        assert not res.location.lng
        assert not res.address
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_GOING
        assert res.organizer
        assert res.subscriber
        assert res.going_count == 1
        assert res.maybe_count == 0
        assert res.organizer_count == 1
        assert res.subscriber_count == 1
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert res.can_edit
        assert not res.can_moderate

        event_id = res.event_id

    with events_session(token2) as api:
        res = api.GetEvent(events_pb2.GetEventReq(event_id=event_id))

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert res.is_online_only
        assert res.link == "https://app.couchers.org/meet/"
        assert not res.location.lat
        assert not res.location.lng
        assert not res.address
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_NOT_GOING
        assert not res.organizer
        assert not res.subscriber
        assert res.going_count == 1
        assert res.maybe_count == 0
        assert res.organizer_count == 1
        assert res.subscriber_count == 1
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert not res.can_edit
        assert res.can_moderate

    with events_session(token3) as api:
        res = api.GetEvent(events_pb2.GetEventReq(event_id=event_id))

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert res.is_online_only
        assert res.link == "https://app.couchers.org/meet/"
        assert not res.location.lat
        assert not res.location.lng
        assert not res.address
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_NOT_GOING
        assert not res.organizer
        assert not res.subscriber
        assert res.going_count == 1
        assert res.maybe_count == 0
        assert res.organizer_count == 1
        assert res.subscriber_count == 1
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert not res.can_edit
        assert not res.can_moderate

    with events_session(token1) as api:
        # in person event can't have a link
        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    photo_key=None,
                    location=events_pb2.Coordinate(
                        lat=0.1,
                        lng=0.2,
                    ),
                    address="Near Null Island",
                    is_online_only=False,
                    link="https://app.couchers.org/meet/",
                    start_time=Timestamp_from_datetime(start_time),
                    end_time=Timestamp_from_datetime(end_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.OFFLINE_EVENT_HAS_LINK

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    photo_key=None,
                    location=None,
                    address=None,
                    is_online_only=True,
                    link="https://app.couchers.org/meet/",
                    start_time=Timestamp_from_datetime(start_time),
                    end_time=Timestamp_from_datetime(end_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.ONLINE_EVENT_MISSING_PARENT_COMMUNITY

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    # title="Dummy Title",
                    content="Dummy content.",
                    photo_key=None,
                    location=events_pb2.Coordinate(
                        lat=0.1,
                        lng=0.1,
                    ),
                    address="Near Null Island",
                    is_online_only=False,
                    link=None,
                    start_time=Timestamp_from_datetime(start_time),
                    end_time=Timestamp_from_datetime(end_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.MISSING_EVENT_TITLE

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    # content="Dummy content.",
                    photo_key=None,
                    location=events_pb2.Coordinate(
                        lat=0.1,
                        lng=0.1,
                    ),
                    address="Near Null Island",
                    is_online_only=False,
                    link=None,
                    start_time=Timestamp_from_datetime(start_time),
                    end_time=Timestamp_from_datetime(end_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.MISSING_EVENT_CONTENT

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    photo_key="nonexistent",
                    location=events_pb2.Coordinate(
                        lat=0.1,
                        lng=0.1,
                    ),
                    address="Near Null Island",
                    is_online_only=False,
                    link=None,
                    start_time=Timestamp_from_datetime(start_time),
                    end_time=Timestamp_from_datetime(end_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.PHOTO_NOT_FOUND

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    photo_key=None,
                    location=None,
                    address="Near Null Island",
                    is_online_only=False,
                    link=None,
                    start_time=Timestamp_from_datetime(start_time),
                    end_time=Timestamp_from_datetime(end_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.MISSING_EVENT_ADDRESS_OR_LOCATION

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    photo_key=None,
                    location=events_pb2.Coordinate(
                        lat=0.1,
                        lng=0.1,
                    ),
                    # address="Near Null Island",
                    is_online_only=False,
                    link=None,
                    start_time=Timestamp_from_datetime(start_time),
                    end_time=Timestamp_from_datetime(end_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.MISSING_EVENT_ADDRESS_OR_LOCATION

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    is_online_only=True,
                    parent_community_id=c_id,
                    link="https://app.couchers.org/meet/",
                    start_time=Timestamp_from_datetime(now() - timedelta(hours=2)),
                    end_time=Timestamp_from_datetime(end_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.EVENT_IN_PAST

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    is_online_only=True,
                    parent_community_id=c_id,
                    link="https://app.couchers.org/meet/",
                    start_time=Timestamp_from_datetime(end_time),
                    end_time=Timestamp_from_datetime(start_time),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.EVENT_ENDS_BEFORE_STARTS

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    is_online_only=True,
                    parent_community_id=c_id,
                    link="https://app.couchers.org/meet/",
                    start_time=Timestamp_from_datetime(now() + timedelta(days=500, hours=2)),
                    end_time=Timestamp_from_datetime(now() + timedelta(days=500, hours=5)),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.EVENT_TOO_FAR_IN_FUTURE

        with pytest.raises(grpc.RpcError) as e:
            api.CreateEvent(
                events_pb2.CreateEventReq(
                    title="Dummy Title",
                    content="Dummy content.",
                    is_online_only=True,
                    parent_community_id=c_id,
                    link="https://app.couchers.org/meet/",
                    start_time=Timestamp_from_datetime(start_time),
                    end_time=Timestamp_from_datetime(now() + timedelta(days=100)),
                    timezone="UTC",
                )
            )
        assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert e.value.details() == errors.EVENT_TOO_LONG


def test_ScheduleEvent(db):
    # test cases:
    # can schedule a new event occurence

    user, token = generate_user()

    with session_scope() as session:
        c_id = create_community(session, 0, 2, "Community", [user], [], None).id

    time_before = now()
    start_time = now() + timedelta(hours=2)
    end_time = start_time + timedelta(hours=3)

    with events_session(token) as api:
        res = api.CreateEvent(
            events_pb2.CreateEventReq(
                title="Dummy Title",
                content="Dummy content.",
                is_online_only=True,
                parent_community_id=c_id,
                link="https://app.couchers.org/meet/",
                start_time=Timestamp_from_datetime(start_time),
                end_time=Timestamp_from_datetime(end_time),
                timezone="UTC",
            )
        )

        new_start_time = now() + timedelta(hours=6)
        new_end_time = new_start_time + timedelta(hours=2)

        res = api.ScheduleEvent(
            events_pb2.ScheduleEventReq(
                event_id=res.event_id,
                content="New event occurence",
                location=events_pb2.Coordinate(
                    lat=0.3,
                    lng=0.2,
                ),
                address="A bit further but still near Null Island",
                start_time=Timestamp_from_datetime(new_start_time),
                end_time=Timestamp_from_datetime(new_end_time),
                timezone="UTC",
            )
        )

        res = api.GetEvent(events_pb2.GetEventReq(event_id=res.event_id))

        assert not res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "New event occurence"
        assert not res.photo_url
        assert not res.is_online_only
        assert not res.link
        assert res.location.lat == 0.3
        assert res.location.lng == 0.2
        assert res.address == "A bit further but still near Null Island"
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user.id
        assert to_aware_datetime(res.start_time) == new_start_time
        assert to_aware_datetime(res.end_time) == new_end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_GOING
        assert res.organizer
        assert res.subscriber
        assert res.going_count == 1
        assert res.maybe_count == 0
        assert res.organizer_count == 1
        assert res.subscriber_count == 1
        assert res.owner_user_id == user.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert res.can_edit
        assert res.can_moderate


def test_UpdateEvent(db):
    # test cases:
    # owner can update
    # community owner can update
    # can't mess up online/in person dichotomy
    # notifies attendees

    # UpdateEventReq
    pass


def test_GetEvent(db):
    # event creator
    user1, token1 = generate_user()
    # community moderator
    user2, token2 = generate_user()
    # third parties
    user3, token3 = generate_user()
    user4, token4 = generate_user()
    user5, token5 = generate_user()
    user6, token6 = generate_user()

    with session_scope() as session:
        c_id = create_community(session, 0, 2, "Community", [user2], [], None).id

    time_before = now()
    start_time = now() + timedelta(hours=2)
    end_time = start_time + timedelta(hours=3)

    with events_session(token1) as api:
        # in person event
        res = api.CreateEvent(
            events_pb2.CreateEventReq(
                title="Dummy Title",
                content="Dummy content.",
                location=events_pb2.Coordinate(
                    lat=0.1,
                    lng=0.2,
                ),
                address="Near Null Island",
                start_time=Timestamp_from_datetime(start_time),
                end_time=Timestamp_from_datetime(end_time),
                timezone="UTC",
            )
        )

        event_id = res.event_id

    with events_session(token4) as api:
        api.SetEventSubscription(events_pb2.SetEventSubscriptionReq(event_id=event_id, subscribe=True))

    with events_session(token5) as api:
        api.SetEventAttendance(
            events_pb2.SetEventAttendanceReq(event_id=event_id, attendance_state=events_pb2.ATTENDANCE_STATE_GOING)
        )

    with events_session(token6) as api:
        api.SetEventSubscription(events_pb2.SetEventSubscriptionReq(event_id=event_id, subscribe=True))
        api.SetEventAttendance(
            events_pb2.SetEventAttendanceReq(event_id=event_id, attendance_state=events_pb2.ATTENDANCE_STATE_MAYBE)
        )

    with events_session(token1) as api:
        res = api.GetEvent(events_pb2.GetEventReq(event_id=event_id))

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert not res.is_online_only
        assert not res.link
        assert res.location.lat == 0.1
        assert res.location.lng == 0.2
        assert res.address == "Near Null Island"
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_GOING
        assert res.organizer
        assert res.subscriber
        assert res.going_count == 2
        assert res.maybe_count == 1
        assert res.organizer_count == 1
        assert res.subscriber_count == 3
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert res.can_edit
        assert not res.can_moderate

    with events_session(token2) as api:
        res = api.GetEvent(events_pb2.GetEventReq(event_id=event_id))

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert not res.is_online_only
        assert not res.link
        assert res.location.lat == 0.1
        assert res.location.lng == 0.2
        assert res.address == "Near Null Island"
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_NOT_GOING
        assert not res.organizer
        assert not res.subscriber
        assert res.going_count == 2
        assert res.maybe_count == 1
        assert res.organizer_count == 1
        assert res.subscriber_count == 3
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert not res.can_edit
        assert res.can_moderate

    with events_session(token3) as api:
        res = api.GetEvent(events_pb2.GetEventReq(event_id=event_id))

        assert res.is_next
        assert not res.is_past
        assert res.is_future
        assert res.title == "Dummy Title"
        assert res.slug == "dummy-title"
        assert res.content == "Dummy content."
        assert not res.photo_url
        assert not res.is_online_only
        assert not res.link
        assert res.location.lat == 0.1
        assert res.location.lng == 0.2
        assert res.address == "Near Null Island"
        assert time_before < to_aware_datetime(res.created) < now()
        assert time_before < to_aware_datetime(res.last_edited) < now()
        assert res.creator_user_id == user1.id
        assert to_aware_datetime(res.start_time) == start_time
        assert to_aware_datetime(res.end_time) == end_time
        # assert res.timezone == "UTC"
        assert res.start_time_display
        assert res.end_time_display
        assert res.attendance_state == events_pb2.ATTENDANCE_STATE_NOT_GOING
        assert not res.organizer
        assert not res.subscriber
        assert res.going_count == 2
        assert res.maybe_count == 1
        assert res.organizer_count == 1
        assert res.subscriber_count == 3
        assert res.owner_user_id == user1.id
        assert not res.owner_community_id
        assert not res.owner_group_id
        assert res.thread_id
        assert not res.can_edit
        assert not res.can_moderate


def test_ListEventAttendees(db):
    # ListEventAttendeesReq
    pass


def test_ListEventSubscribers(db):
    # ListEventSubscribersReq
    pass


def test_ListEventOrganizers(db):
    # ListEventOrganizersReq
    pass


def test_TransferEvent(db):
    # test cases:
    # can transfer from individual to community/group
    # can transfer from community/group to other

    # TransferEventReq
    pass


def test_SetEventSubscription(db):
    # SetEventSubscriptionReq
    pass


def test_SetEventAttendance(db):
    # SetEventAttendanceReq
    pass


def test_InviteEventOrganizer(db):
    # test cases:
    # works and sends email

    # InviteEventOrganizerReq
    pass


def test_InviteEventOrganizer(db):
    # InviteEventOrganizerReq
    pass


def test_ListEventOccurences(db):
    user1, token1 = generate_user()
    user2, token2 = generate_user()
    user3, token3 = generate_user()

    with session_scope() as session:
        c_id = create_community(session, 0, 2, "Community", [user2], [], None).id

    time_before = now()
    start = now()

    event_ids = []

    with events_session(token1) as api:
        res = api.CreateEvent(
            events_pb2.CreateEventReq(
                title="First occurence",
                content="Dummy content.",
                is_online_only=True,
                parent_community_id=c_id,
                link="https://app.couchers.org/meet/",
                start_time=Timestamp_from_datetime(start + timedelta(hours=1)),
                end_time=Timestamp_from_datetime(start + timedelta(hours=1.5)),
                timezone="UTC",
            )
        )

        event_ids.append(res.event_id)

        for i in range(5):
            res = api.ScheduleEvent(
                events_pb2.ScheduleEventReq(
                    event_id=event_ids[-1],
                    content=f"{i}th occurence",
                    is_online_only=True,
                    link="https://app.couchers.org/meet/",
                    start_time=Timestamp_from_datetime(start + timedelta(hours=1 + i)),
                    end_time=Timestamp_from_datetime(start + timedelta(hours=1.5 + i)),
                    timezone="UTC",
                )
            )

            event_ids.append(res.event_id)

        res = api.ListEventOccurences(events_pb2.ListEventOccurencesReq(event_id=event_ids[-1], page_size=2))

        assert [event.event_id for event in res.events] == event_ids[:2]


def test_ListMyEvents(db):
    # ListMyEventsReq
    pass


def test_RemoveEventOrganizer(db):
    # RemoveEventOrganizerReq
    pass
