import java.io.*;
import java.util.*;

class Patient implements Serializable {
    private String name;
    private int age;
    private String gender;
    private String condition;

    public Patient(String name, int age, String gender, String condition) {
        this.name = name;
        this.age = age;
        this.gender = gender;
        this.condition = condition;
    }

    // Getters
    public String getName() {
        return name;
    }

    public int getAge() {
        return age;
    }

    public String getGender() {
        return gender;
    }

    public String getCondition() {
        return condition;
    }
}

class Doctor implements Serializable {
    private String name;
    private String specialty;

    public Doctor(String name, String specialty) {
        this.name = name;
        this.specialty = specialty;
    }

    // Getters
    public String getName() {
        return name;
    }

    public String getSpecialty() {
        return specialty;
    }
}

class Appointment implements Serializable {
    private Doctor doctor;
    private Patient patient;
    private String date;
    private String time;

    public Appointment(Doctor doctor, Patient patient, String date, String time) {
        this.doctor = doctor;
        this.patient = patient;
        this.date = date;
        this.time = time;
    }

    // Getters
    public Doctor getDoctor() {
        return doctor;
    }

    public Patient getPatient() {
        return patient;
    }

    public String getDate() {
        return date;
    }

    public String getTime() {
        return time;
    }
}

class Hospital implements Serializable {
    private String name;
    private List<Patient> patients;
    private List<Doctor> doctors;
    private List<Appointment> appointments;

    public Hospital(String name) {
        this.name = name;
        this.patients = new ArrayList<Patient>(); // Specify type inside ArrayList constructor
        this.doctors = new ArrayList<Doctor>(); // Specify type inside ArrayList constructor
        this.appointments = new ArrayList<Appointment>(); // Specify type inside ArrayList constructor
    }

    public void addPatient(Patient patient) {
        patients.add(patient);
    }

    public void addDoctor(Doctor doctor) {
        doctors.add(doctor);
    }

    public void scheduleAppointment(Doctor doctor, Patient patient, String date, String time) {
        Appointment appointment = new Appointment(doctor, patient, date, time);
        appointments.add(appointment);
        System.out.println("Appointment scheduled for " + patient.getName() + " with Dr. " + doctor.getName() + " on " + date + " at " + time + ".");
    }

    public void listAppointments() {
        System.out.println("List of Appointments:");
        for (Appointment appointment : appointments) {
            System.out.println("Doctor: " + appointment.getDoctor().getName() + ", Patient: " + appointment.getPatient().getName() + ", Date: " + appointment.getDate() + ", Time: " + appointment.getTime());
        }
    }
    
    // Getter methods for doctors, patients, and appointments
    public List<Doctor> getDoctors() {
        return doctors;
    }
    
    public List<Patient> getPatients() {
        return patients;
    }

    public List<Appointment> getAppointments() {
        return appointments;
    }

    // Save data to files
    public void saveData() {
        try {
            // Save doctors to a file
            ObjectOutputStream doctorStream = new ObjectOutputStream(new FileOutputStream("doctors.dat"));
            doctorStream.writeObject(doctors);
            doctorStream.close();

            // Save patients to a file
            ObjectOutputStream patientStream = new ObjectOutputStream(new FileOutputStream("patients.dat"));
            patientStream.writeObject(patients);
            patientStream.close();

            // Save appointments to a file
            ObjectOutputStream appointmentStream = new ObjectOutputStream(new FileOutputStream("appointments.dat"));
            appointmentStream.writeObject(appointments);
            appointmentStream.close();

            System.out.println("Data saved successfully.");
        } catch (IOException e) {
            System.out.println("Error saving data: " + e.getMessage());
        }
    }

     // Retrieve data from files
    public void retrieveData() {
        try {
            // Retrieve doctors from the file
            ObjectInputStream doctorStream = new ObjectInputStream(new FileInputStream("doctors.dat"));
            doctors = (List<Doctor>) doctorStream.readObject();
            doctorStream.close();

            // Retrieve patients from the file
            ObjectInputStream patientStream = new ObjectInputStream(new FileInputStream("patients.dat"));
            patients = (List<Patient>) patientStream.readObject();
            patientStream.close();

            // Retrieve appointments from the file
            ObjectInputStream appointmentStream = new ObjectInputStream(new FileInputStream("appointments.dat"));
            appointments = (List<Appointment>) appointmentStream.readObject();
            appointmentStream.close();

            System.out.println("Data retrieved successfully.");
        } catch (IOException e) {
            System.out.println("Error retrieving data: " + e.getMessage());
        } catch (ClassNotFoundException e) {
            System.out.println("Error retrieving data: " + e.getMessage());
        }
    }

}

public class HospitalManagementSystem 
{
    public static void main(String[] args) 
    {
        Hospital hospital = new Hospital("Example Hospital");
        Scanner scanner = new Scanner(System.in);

        boolean exit = false;

        // Retrieve data from files when starting the program
        hospital.retrieveData();

        System.out.println("\n\n\n\n\t\tWelcome To Hospital Management System\n\n\n\n");

        while (!exit) {
            System.out.println("\nChoose what you want to do:");
            System.out.println("1. Add Doctor");
            System.out.println("2. Add Patient");
            System.out.println("3. Schedule Appointment");
            System.out.println("4. Save Data");
            System.out.println("5. Exit");
            System.out.print("Enter your choice: ");
            int choice = scanner.nextInt();
            scanner.nextLine(); // Consume newline

            switch (choice) {
                case 1:
	                System.out.println("Choose what you want to do");
	                System.out.println("1. Add Doctor");
                 	System.out.println("2. Add Patient");
                	System.out.println("3. Exit");
            	    System.out.print("Enter your choice: ");
           	        int docchoice = scanner.nextInt();
            	    scanner.nextLine(); // Consume newline
	
	                switch(docchoice)
                    {
	                     case 1:     
	                        // Adding doctors
                            System.out.println("\n\n\n\nEnter doctor details:");
                            System.out.print("Name: ");
       	                    String doctorName = scanner.nextLine();
	                        System.out.print("Specialty: ");
	                        String doctorSpecialty = scanner.nextLine();
               	            Doctor doctor = new Doctor(doctorName, doctorSpecialty);
     	                    hospital.addDoctor(doctor);
                            break;
	
                	    case 2:
                	        // Display doctors
                	        System.out.println("Doctors:");
                	        System.out.println("--------------------------------------------------------------");
                	        System.out.printf("| %-20s | %-30s |\n", "Name", "Specialty");
                	        System.out.println("--------------------------------------------------------------");
                	        for (Doctor doctor : hospital.getDoctors()) {
                	        System.out.printf("| %-20s | %-30s |\n", doctor.getName(), doctor.getSpecialty());
                            }
                
                    }
        
                case 2:
                    // Adding patients
                    System.out.println("\n\n\n\nEnter patient details:");
                    System.out.print("Name: ");
                    String patientName = scanner.nextLine();
                    System.out.print("Age: ");
                    int patientAge = scanner.nextInt();
                    scanner.nextLine(); // Consume newline
                    System.out.print("Gender: ");
                    String patientGender = scanner.nextLine();
                    System.out.print("Condition: ");
                    String patientCondition = scanner.nextLine();
                    Patient patient = new Patient(patientName, patientAge, patientGender, patientCondition);
                    hospital.addPatient(patient);
                    break;

                case 3:
                    // Scheduling appointments
                    System.out.println("\n\n\n\nEnter appointment details:");
                    System.out.print("Doctor's name: ");
                    String doctorNameForAppt = scanner.nextLine();
                    Doctor selectedDoctor = null;
                    for (Doctor doc : hospital.getDoctors()) {
                        if (doc.getName().equalsIgnoreCase(doctorNameForAppt)) {
                            selectedDoctor = doc;
                            break;
                        }
                    }
                    if (selectedDoctor == null) {
                        System.out.println("Doctor not found.");
                        break;
                    }
                    System.out.print("Patient's name: ");
                    String patientNameForAppt = scanner.nextLine();
                    Patient selectedPatient = null;
                    for (Patient pat : hospital.getPatients()) {
                        if (pat.getName().equalsIgnoreCase(patientNameForAppt)) {
                            selectedPatient = pat;
                            break;
                        }
                    }
                    if (selectedPatient == null) {
                        System.out.println("Patient not found.");
                        break;
                    }
                    System.out.print("Date (YYYY-MM-DD): ");
                    String date = scanner.nextLine();
                    System.out.print("Time: ");
                    String time = scanner.nextLine();
                    // Code to schedule appointment goes here
                    break;

                case 4:
                    // Save data
                    hospital.saveData();
                    break;

                case 5:
	                //show data
                    System.out.println("\n\n\n\nDisplaying Data in Table Format:");
                    System.out.println("=================================\n")
                    // Display doctors
                    System.out.println("Doctors:");
                    System.out.println("--------------------------------------------------------------");
                    System.out.printf("| %-20s | %-30s |\n", "Name", "Specialty");
                    System.out.println("--------------------------------------------------------------");
                    for (Doctor doctor : hospital.getDoctors()) {
                        System.out.printf("| %-20s | %-30s |\n", doctor.getName(), doctor.getSpecialty());
                    }
                    System.out.println("--------------------------------------------------------------")
                    // Display patients
                    System.out.println("\nPatients:");
                    System.out.println("--------------------------------------------------------------");
                    System.out.printf("| %-20s | %-5s | %-10s | %-30s |\n", "Name", "Age", "Gender", "Condition");
                    System.out.println("--------------------------------------------------------------");
                    for (Patient patient : hospital.getPatients()) {
                        System.out.printf("| %-20s | %-5d | %-10s | %-30s |\n", patient.getName(), patient.getAge(), patient.getGender(), patient.getCondition());
                    }
                    System.out.println("--------------------------------------------------------------")
                    // Display appointments
                    System.out.println("\nAppointments:");
                    System.out.println("--------------------------------------------------------------");
                    System.out.printf("| %-20s | %-20s | %-15s | %-10s |\n", "Doctor", "Patient", "Date", "Time");
                    System.out.println("--------------------------------------------------------------");
                    for (Appointment appointment : hospital.getAppointments()) {
                        System.out.printf("| %-20s | %-20s | %-15s | %-10s |\n", appointment.getDoctor().getName(), appointment.getPatient().getName(), appointment.getDate()appointment.getTime());
                    }
                    System.out.println("--------------------------------------------------------------");
            
	                break;

                case 6:
	                //exit
	                exit = true;
	                break;
	
                default:
	                System.out.println("Invalid choice please enter a number from 1-5");
                	break;
            }
        }
    }
}
}

