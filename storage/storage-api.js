// /storage/storage-api.js
require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { MongoClient, ObjectId } = require('mongodb');
const redis = require('redis');

const app = express();
app.use(bodyParser.json());

const mongoHost = process.env.MONGO_HOST || 'localhost';
const mongoPort = process.env.MONGO_PORT || '27017';
const mongoDbName = process.env.MONGO_DB || 'waze_traffic';
const mongoUri = `mongodb://${mongoHost}:${mongoPort}`;

let dbClient, db;
async function connectMongo() {
  dbClient = new MongoClient(mongoUri, {
    useNewUrlParser: true,
    useUnifiedTopology: true
  });
  await dbClient.connect();
  db = dbClient.db(mongoDbName);
  console.log(`Conectado a MongoDB: ${mongoDbName}`);
}

const cacheHost = 'cache'; // nombre del servicio /cache
const cachePort = 6379;
let redisClient;
async function connectRedis() {
  redisClient = redis.createClient({ url: `redis://${cacheHost}:${cachePort}` });
  redisClient.on('error', err => console.error('Redis Client Error', err));
  await redisClient.connect();
  console.log('Conectado a Redis.');
}

// Middleware: chequea cache antes de GET /jams/:id
async function checkCache(req, res, next) {
  const jamId = req.params.id;
  if (!redisClient) return next();
  try {
    const cached = await redisClient.get(`jam:${jamId}`);
    if (cached) {
      return res.status(200).json(JSON.parse(cached));
    }
    next();
  } catch (err) {
    console.error('Error en cache check:', err);
    next();
  }
}

// POST /jams
app.post('/jams', async (req, res) => {
  try {
    const jam = req.body;
    const result = await db.collection('jams').insertOne(jam);
    // Invalido cache para este jamId (por si ya existía)
    if (redisClient) await redisClient.del(`jam:${jam.idJam}`);
    res.status(201).json({ insertedId: result.insertedId });
  } catch (err) {
    console.error('Error insertando jam:', err);
    res.status(500).json({ error: 'Error insertando jam' });
  }
});

// POST /alerts
app.post('/alerts', async (req, res) => {
  try {
    const alert = req.body;
    const result = await db.collection('alerts').insertOne(alert);
    res.status(201).json({ insertedId: result.insertedId });
  } catch (err) {
    console.error('Error insertando alert:', err);
    res.status(500).json({ error: 'Error insertando alert' });
  }
});

// GET /jams/ids  → devuelve lista de todos los ObjectId como strings
app.get('/jams/ids', async (req, res) => {
  try {
    const docs = await db.collection('jams').find({}, { projection: { _id: 1 } }).toArray();
    const ids = docs.map(d => d._id.toString());
    res.status(200).json({ ids });
  } catch (err) {
    console.error('Error obteniendo IDs de jams:', err);
    res.status(500).json({ error: 'Error obteniendo IDs' });
  }
});

// GET /jams/:id  → chequea cache; si miss, lee de Mongo y guarda en cache
app.get('/jams/:id', checkCache, async (req, res) => {
  try {
    const id = req.params.id;
    const doc = await db.collection('jams').findOne({ _id: new ObjectId(id) });
    if (!doc) return res.status(404).json({ error: 'Jam no encontrado' });
    // Guardamos en cache para próximas lecturas
    if (redisClient) {
      await redisClient.set(`jam:${id}`, JSON.stringify(doc), { EX: 300 });
    }
    res.status(200).json(doc);
  } catch (err) {
    console.error('Error obteniendo jam por ID:', err);
    res.status(500).json({ error: 'Error obteniendo jam por ID' });
  }
});

// (Opcional) Otros endpoints de consulta: por comuna, rango de tiempo, etc.
// Por ejemplo: GET /jams?commune=Santiago&from=2025-05-31T00:00:00Z&to=...

const PORT = process.env.PORT || 4000;
async function startServer() {
  await connectMongo();
  await connectRedis();
  app.listen(PORT, () => {
    console.log(`Storage-API escuchando en puerto ${PORT}`);
  });
}

startServer().catch(err => {
  console.error('Error arrancando Storage-API:', err);
  process.exit(1);
});
