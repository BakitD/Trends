create database if not exists geomap;

use geomap;


create table if not exists placetype (
	id int not null auto_increment primary key,
	name varchar(16) not null,
	unique(name)
);

create table if not exists place (
	id int not null auto_increment primary key,
	name varchar(32) not null,
	woeid varchar(16) not null,
	longitude varchar(32) not null,
	latitude varchar(32) not null,
	parent_id varchar(16) default NULL,
	dtime timestamp not null default 0,
	placetype_id int not null,
	foreign key(placetype_id) references placetype(id)
		on delete cascade,
	unique(woeid)
);

drop trigger if exists before_insert_place;
create trigger before_insert_place
	before insert on place
	for each row
	set new.dtime = date_sub(CURRENT_TIMESTAMP, interval 1 day);


create table if not exists trend (
	id int not null auto_increment primary key,
	name varchar(255) not null,
	volume varchar(32) default null,
	dtime timestamp not null default CURRENT_TIMESTAMP,
	place_id int  not null,
	foreign key(place_id) references place(id)
		on delete cascade
);



insert ignore into placetype (name) values ( 'town');
insert ignore into placetype (name) values ( 'country');
insert ignore into placetype (name) values ( 'worldwide');
insert ignore into placetype (name) values ( 'unknown');





	
