FROM maven:3.9.6-eclipse-temurin-17 AS build

WORKDIR /app

# Copy Maven project files
COPY pom.xml .
COPY src ./src

# Run Maven build
RUN mvn clean package shade:shade -DskipTests

# Create a minimal runtime image
FROM openjdk:17-jdk-slim

WORKDIR /app

# Install tini and bash
RUN apt-get update && \
    apt-get install -y tini bash && \
    rm -rf /var/lib/apt/lists/*

# Copy the built JAR from the first stage
COPY --from=build /app/target/*.jar producer.jar

ENTRYPOINT ["java", "-jar", "producer.jar"]
