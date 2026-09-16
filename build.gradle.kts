plugins {
    `java-library`
    `maven-publish`
}
group = "dev.ctok"
version = "1.3.0-java.1"
repositories { mavenCentral() }
java {
    withSourcesJar()
    withJavadocJar()
}
tasks.withType<JavaCompile>().configureEach { options.release = 21; options.encoding = "UTF-8" }
tasks.javadoc { options.encoding = "UTF-8" }
tasks.jar { manifest { attributes["Main-Class"] = "dev.ctok.CtokCli"; attributes["Automatic-Module-Name"] = "dev.ctok" } }
tasks.processResources { from("LICENSE") { into("META-INF/licenses/ctok") } }
publishing { publications { create<MavenPublication>("library") { from(components["java"]) } } }
val verifyParity by tasks.registering(JavaExec::class) {
    group = "verification"
    description = "Run API checks and optional Python-reference parity corpus (-PparityFile=...)"
    dependsOn(tasks.testClasses)
    classpath = sourceSets.test.get().runtimeClasspath
    mainClass = "dev.ctok.ParityTest"
    providers.gradleProperty("parityFile").orNull?.let { args(it) }
    maxHeapSize = "1g"
}
// Verification is an executable test harness, with no runtime or test-framework dependencies.
tasks.test {
    dependsOn(verifyParity)
    failOnNoDiscoveredTests = false
}
