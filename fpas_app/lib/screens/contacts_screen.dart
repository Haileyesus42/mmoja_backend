import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/contact_model.dart';
import '../widgets/sos_button.dart'; // Import the SOS button widget
// Import auth service
import 'profile_screen.dart'; // Import profile screen

class ContactsScreen extends StatefulWidget {
  const ContactsScreen({super.key});

  @override
  State<ContactsScreen> createState() => _ContactsScreenState();
}

class _ContactsScreenState extends State<ContactsScreen> {
  List<TextEditingController> _nameControllers = [];
  List<TextEditingController> _relationshipControllers = [];
  List<TextEditingController> _phoneControllers = [];
  List<TextEditingController> _whatsappControllers = [];

  bool _isLoading = true;
  bool _isSaving = false;
  String? _errorMessage;
  List<ContactModel> _contacts = [];
  final _formKey = GlobalKey<FormState>(); // Add form key for validation

  @override
  void initState() {
    super.initState();
    _loadContacts();
  }

  @override
  void dispose() {
    for (var controller in _nameControllers) {
      controller.dispose();
    }
    for (var controller in _relationshipControllers) {
      controller.dispose();
    }
    for (var controller in _phoneControllers) {
      controller.dispose();
    }
    for (var controller in _whatsappControllers) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _loadContacts() async {
    setState(() => _isLoading = true);

    try {
      final contacts = await Provider.of<ApiService>(
        context,
        listen: false,
      ).getEmergencyContacts();
      setState(() {
        _contacts = contacts;
        _initializeControllers(contacts);
        _isLoading = false;
      });
    } catch (e) {
      print('Error loading contacts: $e');
      setState(() {
        _errorMessage = 'Failed to load contacts: $e';
        _isLoading = false;
      });
    }
  }

  void _initializeControllers(List<ContactModel> contacts) {
    for (var controller in _nameControllers) {
      controller.dispose();
    }
    for (var controller in _relationshipControllers) {
      controller.dispose();
    }
    for (var controller in _phoneControllers) {
      controller.dispose();
    }
    for (var controller in _whatsappControllers) {
      controller.dispose();
    }

    _nameControllers = contacts
        .map((c) => TextEditingController(text: c.contactName))
        .toList();
    _relationshipControllers = contacts
        .map((c) => TextEditingController(text: c.relationship ?? ''))
        .toList();
    _phoneControllers = contacts
        .map((c) => TextEditingController(text: c.phone ?? ''))
        .toList();
    _whatsappControllers = contacts
        .map((c) => TextEditingController(text: c.whatsapp ?? ''))
        .toList();
  }

  Future<void> _saveContacts() async {
    setState(() => _isSaving = true);

    final updatedContacts = List<ContactModel>.generate(_contacts.length, (
      index,
    ) {
      return _contacts[index].copyWith(
        contactName: _nameControllers[index].text,
        relationship: _relationshipControllers[index].text,
        phone: _phoneControllers[index].text,
        whatsapp: _whatsappControllers[index].text,
      );
    });

    final result = await Provider.of<ApiService>(
      context,
      listen: false,
    ).updateEmergencyContacts(updatedContacts);

    setState(() => _isSaving = false);

    if (result['success']) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Emergency contacts updated successfully!'),
          backgroundColor: Colors.green,
        ),
      );
      // Reload contacts
      await _loadContacts();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['error'] ?? 'Update failed'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Emergency Contacts', style: TextStyle(fontSize: 16)),
        backgroundColor: theme.brightness == Brightness.dark
            ? Colors.grey[900]
            : theme.primaryColor, // Match dashboard app bar
        foregroundColor: Colors.white,
        automaticallyImplyLeading: true, // Show back button
        toolbarHeight: 56, // Compact toolbar like dashboard
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        actions: const [
          SosButton(), // Add SOS button to the app bar
        ],
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          shrinkWrap: true,
          children: [
            DrawerHeader(
              decoration: BoxDecoration(
                color: theme.brightness == Brightness.dark
                    ? Colors.grey[900]
                    : theme.primaryColor,
              ),
              margin: EdgeInsets.zero,
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Icon(Icons.face, size: 32, color: Colors.white),
                  const SizedBox(height: 4),
                  Text(
                    'Emergency Contacts',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    'Face Authentication System',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ],
              ),
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              leading: const Icon(Icons.home, size: 20),
              title: const Text('Dashboard', style: TextStyle(fontSize: 14)),
              dense: true,
              minVerticalPadding: 4,
              onTap: () {
                Navigator.popAndPushNamed(context, '/');
              },
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              leading: const Icon(Icons.person, size: 20),
              title: const Text('Profile', style: TextStyle(fontSize: 14)),
              dense: true,
              minVerticalPadding: 4,
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const ProfileScreen(),
                  ),
                );
              },
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              leading: const Icon(Icons.contacts, size: 20),
              title: const Text('Contacts', style: TextStyle(fontSize: 14)),
              selected: true, // Highlight current page
              dense: true,
              minVerticalPadding: 4,
              onTap: () {
                // Stay on contacts
                Navigator.pop(context);
              },
            ),
          ],
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Display current contacts in scrollable list
                  if (_contacts.isNotEmpty) ...[
                    Expanded(
                      flex: 2,
                      child: RefreshIndicator(
                        onRefresh: _loadContacts,
                        child: ListView.builder(
                          itemCount: _contacts.length,
                          itemBuilder: (context, index) {
                            final contact = _contacts[index];
                            return Card(
                              elevation: 2,
                              margin: const EdgeInsets.only(bottom: 8), // Reduced margin
                              color: theme.brightness == Brightness.dark 
                                ? Colors.grey[850] 
                                : Colors.white, // Use theme-appropriate color
                              child: InkWell(
                                onTap: () {
                                  // Allow editing by tapping the contact card
                                },
                                child: Padding(
                                  padding: const EdgeInsets.all(12.0),
                                  child: Row(
                                    children: [
                                      CircleAvatar(
                                        radius: 20,
                                        backgroundColor: Colors.red,
                                        child: Icon(
                                          Icons.person,
                                          color: Colors.white,
                                          size: 18,
                                        ),
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            Text(
                                              contact.contactName,
                                              style: TextStyle(
                                                fontSize: 14,
                                                fontWeight: FontWeight.bold,
                                                color: theme.primaryColor,
                                              ),
                                            ),
                                            const SizedBox(height: 2),
                                            Text(
                                              '${contact.relationship ?? "Contact"} • Priority ${contact.priority}',
                                              style: TextStyle(
                                                fontSize: 11,
                                                color: theme.brightness == Brightness.dark 
                                                  ? Colors.grey[400] 
                                                  : Colors.grey,
                                              ),
                                            ),
                                            const SizedBox(height: 2),
                                            Text(
                                              '📞 ${contact.phone ?? "No phone"} • 💬 ${contact.whatsapp ?? "No WhatsApp"}',
                                              style: TextStyle(
                                                fontSize: 10,
                                                color: theme.brightness == Brightness.dark 
                                                  ? Colors.grey[500] 
                                                  : Colors.grey[600],
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Icon(
                                        Icons.arrow_forward_ios,
                                        color: theme.brightness == Brightness.dark 
                                          ? Colors.grey[600] 
                                          : Colors.grey[600],
                                        size: 14,
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ),
                  ] else ...[
                    Expanded(
                      flex: 1,
                      child: Center(
                        child: Text(
                          'No emergency contacts found',
                          style: TextStyle(
                            color: theme.brightness == Brightness.dark 
                              ? Colors.grey[400] 
                              : Colors.grey[600],
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ),
                    ),
                  ],

                  // Edit form section - now properly constrained
                  Expanded(
                    flex: 3,
                    child: Card(
                      elevation: 2,
                      margin: const EdgeInsets.only(top: 8), // Reduced margin
                      color: theme.brightness == Brightness.dark 
                        ? Colors.grey[850] 
                        : Colors.white, // Use theme-appropriate color
                      child: Padding(
                        padding: const EdgeInsets.all(12.0), // Reduced padding
                        child: Scrollbar(
                          child: SingleChildScrollView(
                            child: Form( // Wrap the form content in a Form widget
                              key: _formKey,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Edit Contacts',
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  ..._buildEditForms(),

                                  const SizedBox(height: 12), // Reduced gap

                                  // Save button
                                  Align(
                                    alignment: Alignment.centerRight,
                                    child: ElevatedButton(
                                      onPressed: _isSaving
                                          ? null
                                          : () {
                                              if (_formKey.currentState?.validate() ?? false) {
                                                _saveContacts();
                                              }
                                            },
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: theme.primaryColor,
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 16,
                                          vertical: 8,
                                        ),
                                      ),
                                      child: _isSaving
                                          ? const SizedBox(
                                              height: 16,
                                              width: 16,
                                              child: CircularProgressIndicator(
                                                strokeWidth: 2,
                                                valueColor:
                                                    AlwaysStoppedAnimation<Color>(Colors.white),
                                              ),
                                            )
                                          : const Text(
                                              'Save Contacts',
                                              style: TextStyle(
                                                color: Colors.white,
                                              ),
                                            ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),

                  // Error Message
                  if (_errorMessage != null) ...[
                    Container(
                      margin: const EdgeInsets.only(top: 6), // Reduced margin
                      padding: const EdgeInsets.all(8), // Reduced padding
                      decoration: BoxDecoration(
                        color: const Color(0x00fee2e2),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: const Color(0xFFFECAAA)),
                      ),
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(
                          color: Color(0xFF991B1B),
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
      ),
    );
  }

  List<Widget> _buildEditForms() {
    if (_contacts.isEmpty ||
        _nameControllers.length != _contacts.length ||
        _relationshipControllers.length != _contacts.length ||
        _phoneControllers.length != _contacts.length ||
        _whatsappControllers.length != _contacts.length) {
      return [];
    }

    return List.generate(_contacts.length, (index) {
      return Container(
        margin: const EdgeInsets.only(bottom: 8), // Reduced margin
        padding: const EdgeInsets.all(10), // Reduced padding
        decoration: BoxDecoration(
          color: Theme.of(context).brightness == Brightness.dark 
            ? Colors.grey[800] 
            : Colors.white, // Theme-appropriate background, no border
          borderRadius: BorderRadius.circular(6),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Contact ${index + 1} (Priority ${_contacts[index].priority})',
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8), // Reduced gap
            TextFormField(
              controller: _nameControllers[index],
              decoration: InputDecoration(
                labelText: 'Contact Name',
                hintText: 'Enter contact name',
                border: const OutlineInputBorder(),
                filled: true, // Ensure proper theming
                fillColor: Theme.of(context).brightness == Brightness.dark 
                  ? Colors.grey[750] 
                  : Colors.white, // Theme-appropriate input background
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please enter contact name';
                }
                return null;
              },
            ),
            const SizedBox(height: 8), // Reduced gap
            TextFormField(
              controller: _relationshipControllers[index],
              decoration: InputDecoration(
                labelText: 'Relationship',
                hintText: 'Enter relationship',
                border: const OutlineInputBorder(),
                filled: true, // Ensure proper theming
                fillColor: Theme.of(context).brightness == Brightness.dark 
                  ? Colors.grey[750] 
                  : Colors.white, // Theme-appropriate input background
              ),
            ),
            const SizedBox(height: 8), // Reduced gap
            TextFormField(
              controller: _phoneControllers[index],
              decoration: InputDecoration(
                labelText: 'Phone',
                hintText: 'Enter phone number',
                border: const OutlineInputBorder(),
                filled: true, // Ensure proper theming
                fillColor: Theme.of(context).brightness == Brightness.dark 
                  ? Colors.grey[750] 
                  : Colors.white, // Theme-appropriate input background
              ),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 8), // Reduced gap
            TextFormField(
              controller: _whatsappControllers[index],
              decoration: InputDecoration(
                labelText: 'WhatsApp',
                hintText: 'Enter WhatsApp number',
                border: const OutlineInputBorder(),
                filled: true, // Ensure proper theming
                fillColor: Theme.of(context).brightness == Brightness.dark 
                  ? Colors.grey[750] 
                  : Colors.white, // Theme-appropriate input background
              ),
              keyboardType: TextInputType.phone,
            ),
          ],
        ),
      );
    });
  }
}