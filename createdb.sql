create database if not exists geomap;

use geomap;


create table if not exists placetype (
	id int not null auto_increment primary key,
	name varchar(16) not null,
	unique(name)
);

create table if not exists layer (
	id int not null auto_increment primary key,
	name varchar(64) not null,
	scale int not null,
	unique(name),
	unique(scale)
);

create table if not exists place (
	id int not null auto_increment primary key,
	name varchar(64) not null,
	another_name varchar(64) default null,
	woeid varchar(16) not null,
	longitude varchar(32) not null,
	latitude varchar(32) not null,
	dtime timestamp not null default CURRENT_TIMESTAMP,
	parent_id varchar(16) default NULL,
	placetype_id int not null,
	layer_id int default null,
	foreign key(layer_id) references layer(id) on update cascade,
	foreign key(placetype_id) references placetype(id) on delete cascade,
	unique(woeid)
);


create table if not exists trend (
	id int not null auto_increment primary key,
	name varchar(255) not null,
	unique(name)
);


create table if not exists geotrend (
	id int not null auto_increment primary key,
	dtime timestamp not null default CURRENT_TIMESTAMP,
	volume int default null,
	trend_id int not null,
	place_id int not null,
	foreign key(place_id) references place(id) on delete cascade,
	foreign key(trend_id) references trend(id) on delete cascade,
	unique(place_id, trend_id, dtime)
);

create table if not exists clusters (
	id int not null auto_increment primary key,
	name varchar(255) not null,
	valid boolean not null default 0,
	unique(name)
);

create table if not exists word (
	id int not null auto_increment primary key,
	name varchar(255) binary not null unique,
	clusters_id int not null,
	foreign key(clusters_id) references clusters(id) on delete cascade
);

create table if not exists trendword (
	id int not null auto_increment primary key,
	trend_id int not null,
	word_id int not null,
	foreign key(word_id) references word(id) on delete cascade,
	foreign key(trend_id) references trend(id) on delete cascade,
	unique(word_id, trend_id)
);

insert ignore into layer (name, scale) values ('initial', 0);
insert ignore into layer (name, scale) values ('first', 6);
insert ignore into layer (name, scale) values ('second', 8);


insert ignore into placetype (name) values ( 'town');
insert ignore into placetype (name) values ( 'country');
insert ignore into placetype (name) values ( 'worldwide');
insert ignore into placetype (name) values ( 'unknown');





	
