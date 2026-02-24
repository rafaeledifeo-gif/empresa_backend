--
-- PostgreSQL database dump
--

\restrict nNFcDRzeJxyIGOImWK8h7YydjqpefyvFtZTTJgm2sq0yjLKbfYOaVk2SMKllKuH

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: clientes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clientes (
    id character varying NOT NULL,
    nombre character varying NOT NULL,
    email character varying,
    hashed_password character varying NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT now()
);


ALTER TABLE public.clientes OWNER TO postgres;

--
-- Name: empresas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.empresas (
    id character varying NOT NULL,
    nombre character varying NOT NULL,
    descripcion character varying,
    direccion character varying,
    cantidad_sedes integer,
    cantidad_usuarios integer,
    fecha_creacion timestamp without time zone DEFAULT now(),
    ultima_actualizacion timestamp without time zone
);


ALTER TABLE public.empresas OWNER TO postgres;

--
-- Name: funcion_servicio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.funcion_servicio (
    funcion_id character varying NOT NULL,
    servicio_id character varying NOT NULL
);


ALTER TABLE public.funcion_servicio OWNER TO postgres;

--
-- Name: funciones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.funciones (
    id character varying NOT NULL,
    nombre character varying NOT NULL,
    descripcion character varying,
    sede_id character varying NOT NULL
);


ALTER TABLE public.funciones OWNER TO postgres;

--
-- Name: locaciones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.locaciones (
    id character varying NOT NULL,
    nombre character varying NOT NULL,
    descripcion character varying,
    sede_id character varying NOT NULL,
    ultima_actualizacion timestamp without time zone
);


ALTER TABLE public.locaciones OWNER TO postgres;

--
-- Name: sedes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sedes (
    id character varying NOT NULL,
    nombre character varying NOT NULL,
    direccion character varying,
    ciudad character varying,
    telefono character varying,
    empresa_id character varying,
    ultima_actualizacion timestamp without time zone
);


ALTER TABLE public.sedes OWNER TO postgres;

--
-- Name: servicios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.servicios (
    id character varying NOT NULL,
    nombre character varying NOT NULL,
    descripcion character varying,
    identificador_letra character varying NOT NULL,
    rango_inicio integer NOT NULL,
    rango_fin integer NOT NULL,
    contador_actual integer NOT NULL,
    ultima_generacion timestamp without time zone DEFAULT now(),
    sede_id character varying NOT NULL,
    activo boolean
);


ALTER TABLE public.servicios OWNER TO postgres;

--
-- Name: tickets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tickets (
    id character varying NOT NULL,
    codigo character varying NOT NULL,
    servicio_id character varying NOT NULL,
    notas character varying,
    estado character varying,
    hora_creacion timestamp without time zone DEFAULT now(),
    hora_llamado timestamp without time zone,
    hora_cierre timestamp without time zone,
    sede_id character varying NOT NULL,
    puesto_nombre character varying(255)
);


ALTER TABLE public.tickets OWNER TO postgres;

--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id character varying NOT NULL,
    nombre character varying NOT NULL,
    apellido character varying,
    username character varying NOT NULL,
    password character varying NOT NULL,
    perfil character varying NOT NULL,
    estado character varying NOT NULL,
    funcion_id character varying,
    empresa_id character varying,
    sede_id character varying,
    ultima_actualizacion timestamp without time zone
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes (id, nombre, email, hashed_password, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: empresas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.empresas (id, nombre, descripcion, direccion, cantidad_sedes, cantidad_usuarios, fecha_creacion, ultima_actualizacion) FROM stdin;
1768764886428	Aledo	Prueba 1	Casalvelino	1	0	2026-01-18 19:34:46.518959	2026-01-18 19:57:02.026217
\.


--
-- Data for Name: funcion_servicio; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.funcion_servicio (funcion_id, servicio_id) FROM stdin;
1768768370102	1768767097468
1768768388665	1768767083074
1768768403163	1768767097468
1768768403163	1768767113376
\.


--
-- Data for Name: funciones; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.funciones (id, nombre, descripcion, sede_id) FROM stdin;
1768768370102	Caja	Cajero	1768766221956
1768768388665	Atencion	Atencion	1768766221956
1768768403163	Servicios	Varios	1768766221956
\.


--
-- Data for Name: locaciones; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.locaciones (id, nombre, descripcion, sede_id, ultima_actualizacion) FROM stdin;
1768768954863	Taquilla 1	Caja	1768766221956	\N
1768768965854	Taquilla 2	Servicios	1768766221956	\N
\.


--
-- Data for Name: sedes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sedes (id, nombre, direccion, ciudad, telefono, empresa_id, ultima_actualizacion) FROM stdin;
1768766221956	Principal	Via velina	Casalvelino	3473774606	1768764886428	\N
\.


--
-- Data for Name: servicios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.servicios (id, nombre, descripcion, identificador_letra, rango_inicio, rango_fin, contador_actual, ultima_generacion, sede_id, activo) FROM stdin;
1768767097468	Caja	Servicio creado manualmente	C	500	600	501	2026-01-18 21:11:37.49356	1768766221956	t
1768767083074	Atencion al cliente	Servicio creado manualmente	A	100	200	101	2026-01-18 21:11:23.440236	1768766221956	t
1768767113376	Pagos	Servicio creado manualmente	P	700	800	702	2026-01-23 00:00:00	1768766221956	t
\.


--
-- Data for Name: tickets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tickets (id, codigo, servicio_id, notas, estado, hora_creacion, hora_llamado, hora_cierre, sede_id, puesto_nombre) FROM stdin;
a89e44b0-daf3-4aa9-bb66-e5f115706ed5	C-500	1768767097468	Hola	cerrado	2026-01-18 21:19:27.035891	2026-01-18 22:19:41.522695	2026-01-18 22:19:44.616965	1768766221956	\N
53439f5b-cdd0-4a20-ab3f-c73acb181e09	P-700	1768767113376		cerrado	2026-01-18 21:19:35.137368	2026-01-19 17:07:27.651024	2026-01-19 17:07:30.619217	1768766221956	\N
0528acce-a494-4194-9f27-2d6693b604e7	A-100	1768767083074		cerrado	2026-01-18 21:19:39.714875	2026-01-19 17:07:29.255711	2026-01-19 17:07:32.045356	1768766221956	\N
98608a68-1934-4b02-bf71-53c889de6360	P-700	1768767113376		cerrado	2026-01-19 17:15:02.541001	2026-01-19 21:58:24.597896	2026-01-19 21:58:29.739841	1768766221956	\N
673815d9-5629-496f-acd5-f7f110f0a69a	P-701	1768767113376		cerrado	2026-01-19 20:58:21.818983	2026-01-19 21:58:28.306715	2026-01-19 21:58:31.351749	1768766221956	\N
69288684-9b08-41dd-9288-09acb9ecb990	P-700	1768767113376		cerrado	2026-01-23 11:10:23.315347	2026-01-23 12:10:25.709323	2026-01-23 12:10:28.718986	1768766221956	\N
c149269b-f38d-46c5-ac73-e6d2594ba72e	P-701	1768767113376		cerrado	2026-01-23 11:11:23.442229	2026-01-23 12:11:39.761589	2026-01-23 12:12:09.427453	1768766221956	\N
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, nombre, apellido, username, password, perfil, estado, funcion_id, empresa_id, sede_id, ultima_actualizacion) FROM stdin;
1768770944724	edoardo	di feo	edo@edo.com	Aledo242529!	Super Administrador	Activo	\N	1768764886428	1768766221956	\N
\.


--
-- Name: clientes clientes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_pkey PRIMARY KEY (id);


--
-- Name: empresas empresas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_pkey PRIMARY KEY (id);


--
-- Name: funcion_servicio funcion_servicio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.funcion_servicio
    ADD CONSTRAINT funcion_servicio_pkey PRIMARY KEY (funcion_id, servicio_id);


--
-- Name: funciones funciones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.funciones
    ADD CONSTRAINT funciones_pkey PRIMARY KEY (id);


--
-- Name: locaciones locaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locaciones
    ADD CONSTRAINT locaciones_pkey PRIMARY KEY (id);


--
-- Name: sedes sedes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sedes
    ADD CONSTRAINT sedes_pkey PRIMARY KEY (id);


--
-- Name: servicios servicios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios
    ADD CONSTRAINT servicios_pkey PRIMARY KEY (id);


--
-- Name: tickets tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_username_key UNIQUE (username);


--
-- Name: ix_clientes_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_clientes_email ON public.clientes USING btree (email);


--
-- Name: ix_clientes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_clientes_id ON public.clientes USING btree (id);


--
-- Name: ix_empresas_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_empresas_id ON public.empresas USING btree (id);


--
-- Name: ix_funciones_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_funciones_id ON public.funciones USING btree (id);


--
-- Name: ix_locaciones_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_locaciones_id ON public.locaciones USING btree (id);


--
-- Name: ix_sedes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sedes_id ON public.sedes USING btree (id);


--
-- Name: ix_servicios_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_servicios_id ON public.servicios USING btree (id);


--
-- Name: ix_tickets_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tickets_id ON public.tickets USING btree (id);


--
-- Name: ix_usuarios_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_usuarios_id ON public.usuarios USING btree (id);


--
-- Name: funcion_servicio funcion_servicio_funcion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.funcion_servicio
    ADD CONSTRAINT funcion_servicio_funcion_id_fkey FOREIGN KEY (funcion_id) REFERENCES public.funciones(id);


--
-- Name: funcion_servicio funcion_servicio_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.funcion_servicio
    ADD CONSTRAINT funcion_servicio_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicios(id);


--
-- Name: funciones funciones_sede_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.funciones
    ADD CONSTRAINT funciones_sede_id_fkey FOREIGN KEY (sede_id) REFERENCES public.sedes(id);


--
-- Name: locaciones locaciones_sede_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.locaciones
    ADD CONSTRAINT locaciones_sede_id_fkey FOREIGN KEY (sede_id) REFERENCES public.sedes(id);


--
-- Name: sedes sedes_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sedes
    ADD CONSTRAINT sedes_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: servicios servicios_sede_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios
    ADD CONSTRAINT servicios_sede_id_fkey FOREIGN KEY (sede_id) REFERENCES public.sedes(id);


--
-- Name: tickets tickets_sede_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_sede_id_fkey FOREIGN KEY (sede_id) REFERENCES public.sedes(id);


--
-- Name: tickets tickets_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicios(id);


--
-- Name: usuarios usuarios_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id);


--
-- Name: usuarios usuarios_funcion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_funcion_id_fkey FOREIGN KEY (funcion_id) REFERENCES public.funciones(id);


--
-- Name: usuarios usuarios_sede_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_sede_id_fkey FOREIGN KEY (sede_id) REFERENCES public.sedes(id);


--
-- PostgreSQL database dump complete
--

\unrestrict nNFcDRzeJxyIGOImWK8h7YydjqpefyvFtZTTJgm2sq0yjLKbfYOaVk2SMKllKuH

