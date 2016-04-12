create database if not exists geomap;

use geomap


create table if not exists placetype (
	id int not null auto_increment primary key,
	name varchar(16) not null
);

create table if not exists place (
	id int not null auto_increment primary key,
	name varchar(32) not null,
	woeid varchar(16) not null,
	parent_id varchar(16) default NULL,
	datetime timestamp default CURRENT_TIMESTAMP,
	placetype_id int not null,
	foreign key(placetype_id) references placetype(id)
		on delete cascade,
	unique(name),
	unique(woeid)
);

create table if not exists trend (
	id int not null auto_increment primary key,
	name varchar(255) not null,
	volume varchar(32) default null,
	place_id int  not null,
	foreign key(place_id) references place(id)
		on delete cascade
);



	
