import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.serialization.StringSerializer;
import java.util.concurrent.locks.LockSupport;

import java.io.*;
import java.util.*;
import java.util.Properties;

public class RateLimitedKafkaProducer {

    public static void main(String[] args) {
        String bootstrapServers = System.getenv().getOrDefault("KAFKA_BROKER", "localhost:9092");
        String topic = System.getenv().getOrDefault("TOPIC_NAME", "default_topic");
        String filePath = System.getenv().getOrDefault("DATA_FILE", "data.txt");

        int maxTuples = Integer.parseInt(System.getenv().getOrDefault("MAX_TUPLES", "100000"));
        int messagesPerSecond = Integer.parseInt(System.getenv().getOrDefault("RATE_LIMIT", "1000"));
        int threads = Integer.parseInt(System.getenv().getOrDefault("PRODUCER_THREADS", "4"));

        // Priorize values from passed arguments

        for (String arg : args) {
            if (arg.startsWith("--broker=")) bootstrapServers = arg.substring("--broker=".length());
            if (arg.startsWith("--topic=")) topic = arg.substring("--topic=".length());
            if (arg.startsWith("--file=")) filePath = arg.substring("--file=".length());

            if (arg.startsWith("--maxTuples=")) maxTuples = Integer.parseInt(arg.substring("--maxTuples=".length()));
            if (arg.startsWith("--rate=")) messagesPerSecond = Integer.parseInt(arg.substring("--rate=".length()));
            if (arg.startsWith("--threads=")) threads = Integer.parseInt(arg.substring("--threads=".length()));
        }

        long intervalNs = 1_000_000_000 / messagesPerSecond;

        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.ACKS_CONFIG, "1");
        props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "none");

        System.out.println("Starting producer with:");
        System.out.println("Kafka Broker: " + bootstrapServers);
        System.out.println("Topic: " + topic);
        System.out.println("Data File: " + filePath);
        System.out.println("Rate Limit: " + messagesPerSecond + " messages/sec");
        System.out.println("Max Tuples " + maxTuples);
        System.out.println("Producer Threads " + threads);

        // Read all lines first

        List<String> lines = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line;
            while ((line = br.readLine()) != null) {
                lines.add(line);
                if (lines.size() >= maxTuples) break;
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

        Producer<String, String> producer = new KafkaProducer<>(props);

        // Produce data in parallel

        try {
            Thread[] producerThreads = new Thread[threads];
            for (int i = 0; i < threads; i++) {
                int threadId = i;
                int threadCount = threads;
                long sleepPerThread  = intervalNs * threadCount;
                String topicName = topic;

                producerThreads[i] = new Thread(() -> produceMessages(lines, producer, topicName, threadId, sleepPerThread, threadCount));
                producerThreads[i].start();
            }

            // Wait for threads to finish
            for (Thread t : producerThreads) {
                t.join();
            }

        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            producer.close();
        }

        System.out.println("Completed");
    }

    private static void produceMessages(List<String> lines, Producer<String, String> producer, String topic, int startOffset, long intervalNs, int threadCount) {
        // Threads will produce line by line alternating

        int totalMessages = lines.size();

        for (int i = startOffset; i < totalMessages; i += threadCount) {
            long startTime = System.nanoTime();

            ProducerRecord<String, String> record = new ProducerRecord<>(topic, lines.get(i));
            producer.send(record, (metadata, exception) -> {
                if (exception != null) {
                    System.err.println("Error sending message: " + exception.getMessage());
                }
            });

            long elapsedTime = System.nanoTime() - startTime;
            long sleepTime = intervalNs - elapsedTime;

            if (sleepTime > 0) {
                LockSupport.parkNanos(sleepTime);
            }
        }
    }
}
